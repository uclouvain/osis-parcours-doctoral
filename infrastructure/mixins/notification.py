# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
import datetime
from typing import Optional, TypedDict

from django.conf import settings
from django.utils.functional import Promise, lazy
from django.utils.translation import get_language, override
from osis_async.models import AsyncTask
from osis_notification.contrib.handlers import WebNotificationHandler
from osis_notification.contrib.notification import WebNotification

from admission.utils import get_doctoral_cdd_managers
from base.forms.utils.datefield import DATE_FORMAT, DATETIME_FORMAT
from base.models.person import Person
from parcours_doctoral.models import (
    JuryMember,
    ParcoursDoctoral,
    ParcoursDoctoralSupervisionActor,
)
from parcours_doctoral.models.task import ParcoursDoctoralTask


class NotificationMixin:
    ADRE_EMAIL = 'adre@uclouvain.be'
    ADRI_EMAIL = 'adri@uclouvain.be'

    @classmethod
    def _format_date(cls, date: Optional[datetime.date]) -> str:
        """Format the date to be used in email notifications"""
        return datetime.date.strftime(date, DATE_FORMAT) if date else ''

    @classmethod
    def _format_datetime(cls, date_time: Optional[datetime.datetime]) -> str:
        """Format the datetime to be used in email notifications"""
        return datetime.date.strftime(date_time, DATETIME_FORMAT) if date_time else ''

    @classmethod
    def _get_supervision_actor_email_cc(cls, parcours_doctoral: ParcoursDoctoral):
        """Get the emails of the supervision actors and concatenate them to be used in email notifications"""
        actors = ParcoursDoctoralSupervisionActor.objects.filter(
            process_id=parcours_doctoral.supervision_group_id
        ).select_related('person')

        return ','.join(["{a.first_name} {a.last_name} <{a.email}>".format(a=actor) for actor in actors])

    @classmethod
    def _get_parcours_doctoral_title_translation(cls, parcours_doctoral: ParcoursDoctoral) -> Promise:
        """Populate the translations of the parcours_doctoral title and lazy return them"""
        # Create a dict to cache the translations of the parcours_doctoral title
        parcours_doctoral_title = {
            settings.LANGUAGE_CODE_EN: parcours_doctoral.training.title_english,
            settings.LANGUAGE_CODE_FR: parcours_doctoral.training.title,
        }

        # Return a lazy proxy which, when evaluated to string, return the correct translation given the current language
        return lazy(lambda: parcours_doctoral_title[get_language()], str)()

    @classmethod
    def _send_notification_to_managers(cls, education_group_id: int, content: str, tokens: dict) -> None:
        """
        Send a web notification to the CDD managers of the given education group
        :param education_group_id: The education group id
        :param content: The content of the notification
        :param tokens: The tokens to be used in the content of the notification
        """
        for manager in get_doctoral_cdd_managers(education_group_id):
            with override(manager.language):
                web_notification = WebNotification(recipient=manager, content=str(content % tokens))
            WebNotificationHandler.create(web_notification)

    @classmethod
    def _create_async_task(
        cls,
        task_name: str,
        task_description: str,
        task_type: ParcoursDoctoralTask.TaskType,
        parcours_doctoral: ParcoursDoctoral,
        person: Person,
    ):
        """Create an async task and link it to the given doctorate"""
        task = AsyncTask.objects.create(
            name=task_name,
            description=task_description,
            person=person,
        )
        ParcoursDoctoralTask.objects.create(
            task=task,
            parcours_doctoral=parcours_doctoral,
            type=task_type.name,
        )

    class JuryMemberInfo(TypedDict):
        person: Optional[Person]
        first_name: str
        last_name: str
        language: str
        email: str

    @classmethod
    def get_jury_member_info(cls, jury_member: JuryMember) -> JuryMemberInfo:
        """
        From a jury member, return a dictionary containing the related person object, if any, the first name,
        last name, language and email address.

        :rtype: JuryMemberInfo
        :param jury_member: The jury member to inspect
        :return: The dictionary containing the info
        """
        info: cls.JuryMemberInfo = {
            'person': None,
            'first_name': '',
            'last_name': '',
            'language': '',
            'email': '',
        }

        if jury_member.promoter_id:
            if jury_member.promoter.person:
                info['person'] = jury_member.promoter.person

            info['first_name'] = jury_member.promoter.first_name
            info['last_name'] = jury_member.promoter.last_name
            info['email'] = jury_member.promoter.email
            info['language'] = jury_member.promoter.language

        elif jury_member.person_id:
            info['person'] = jury_member.person
            info['first_name'] = jury_member.person.first_name
            info['last_name'] = jury_member.person.last_name
            info['email'] = jury_member.person.email
            info['language'] = jury_member.person.language

        else:
            info['first_name'] = jury_member.first_name
            info['last_name'] = jury_member.last_name
            info['email'] = jury_member.email

        return info
