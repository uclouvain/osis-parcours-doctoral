# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from email.message import EmailMessage

from django.conf import settings
from django.shortcuts import resolve_url
from django.utils.functional import lazy
from django.utils.translation import get_language

from admission.models import SupervisionActor
from admission.models.enums.actor_type import ActorType
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoral
from parcours_doctoral.ddd.domain.service.i_notification import INotification
from osis_mail_template.utils import transform_html_to_text
from osis_notification.contrib.handlers import EmailNotificationHandler
from osis_notification.contrib.notification import EmailNotification

from parcours_doctoral.models.parcours_doctoral import ParcoursDoctoral as ParcoursDoctoralModel


class Notification(INotification):
    @classmethod
    def envoyer_message(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_emetteur: str,
        matricule_doctorant: str,
        sujet: str,
        message: str,
        cc_promoteurs: bool,
        cc_membres_ca: bool,
    ) -> EmailMessage:
        parcours_doctoral_instance = ParcoursDoctoralModel.objects.get(uuid=parcours_doctoral.entity_id.uuid)

        # Notifier le doctorant via mail
        email_message = EmailNotificationHandler.build(
            EmailNotification(
                parcours_doctoral_instance.student,
                sujet,
                transform_html_to_text(message),
                message,
            )
        )
        actors = SupervisionActor.objects.filter(process=parcours_doctoral_instance.supervision_group).select_related('person')
        cc_list = []
        if cc_promoteurs:
            for promoter in actors.filter(type=ActorType.PROMOTER.name):
                cc_list.append(cls._format_email(promoter))
        if cc_membres_ca:
            for ca_member in actors.filter(type=ActorType.CA_MEMBER.name):
                cc_list.append(cls._format_email(ca_member))
        if cc_list:
            email_message['Cc'] = ','.join(cc_list)
        EmailNotificationHandler.create(email_message, person=parcours_doctoral_instance.student)

        return email_message

    @classmethod
    def _get_parcours_doctoral_title_translation(cls, parcours_doctoral: ParcoursDoctoralModel):
        """Populate the translations of parcours_doctoral title and lazy return them"""
        # Create a dict to cache the translations of the parcours_doctoral title
        parcours_doctoral_title = {
            settings.LANGUAGE_CODE_EN: parcours_doctoral.training.title_english,
            settings.LANGUAGE_CODE_FR: parcours_doctoral.training.title,
        }

        # Return a lazy proxy which, when evaluated to string, return the correct translation given the current language
        return lazy(lambda: parcours_doctoral_title[get_language()], str)()

    @classmethod
    def get_common_tokens(cls, parcours_doctoral: ParcoursDoctoralModel):
        """Return common tokens about a submission"""
        return {
            "candidate_first_name": parcours_doctoral.student.first_name,
            "candidate_last_name": parcours_doctoral.student.last_name,
            "training_title": cls._get_parcours_doctoral_title_translation(parcours_doctoral),
            "admission_link_front": settings.ADMISSION_FRONTEND_LINK.format(context='parcours_doctoral', uuid=parcours_doctoral.uuid),
            "admission_link_back": "{}{}".format(
                settings.ADMISSION_BACKEND_LINK_PREFIX,
                resolve_url('admission:parcours_doctoral:project', uuid=parcours_doctoral.uuid),
            ),
        }

    @classmethod
    def _format_email(cls, actor: SupervisionActor):
        return "{a.first_name} {a.last_name} <{a.email}>".format(a=actor)
