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

from django.conf import settings
from django.utils.translation import override
from osis_notification.contrib.handlers import EmailNotificationHandler
from osis_notification.contrib.notification import EmailNotification

from ddd.logic.shared_kernel.personne_connue_ucl.dtos import PersonneConnueUclDTO
from parcours_doctoral.ddd.defense_privee.domain.service.i_notification import (
    INotification,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoral
from parcours_doctoral.infrastructure.mixins.notification import NotificationMixin
from parcours_doctoral.mail_templates.private_defense import (
    PARCOURS_DOCTORAL_EMAIL_PRIVATE_DEFENSE_JURY_INVITATION,
)
from parcours_doctoral.models import JuryMember
from parcours_doctoral.models import ParcoursDoctoral as ParcoursDoctoralDBModel
from parcours_doctoral.utils.mail_templates import get_email_templates_by_language
from parcours_doctoral.utils.url import (
    get_parcours_doctoral_link_back,
    get_parcours_doctoral_link_front,
)


class Notification(NotificationMixin, INotification):
    @classmethod
    def get_doctorate(cls, doctorate_uuid):
        return (
            ParcoursDoctoralDBModel.objects.select_related(
                'student',
                'training',
                'current_private_defense',
            )
            .annotate_training_management_entity_title()
            .get(uuid=doctorate_uuid)
        )

    @classmethod
    def get_common_tokens(
        cls,
        doctorate: ParcoursDoctoralDBModel,
        sender_first_name: str,
        sender_last_name: str,
    ) -> dict:
        """Return common tokens about a parcours doctoral"""
        return {
            'student_first_name': doctorate.student.first_name,
            'student_last_name': doctorate.student.last_name,
            'training_title': cls._get_parcours_doctoral_title_translation(doctorate),
            'parcours_doctoral_link_front': get_parcours_doctoral_link_front(doctorate.uuid),
            'parcours_doctoral_link_back': get_parcours_doctoral_link_back(doctorate.uuid),
            'private_defense_link_front': get_parcours_doctoral_link_front(doctorate.uuid, 'private-defense'),
            'private_defense_link_back': get_parcours_doctoral_link_back(doctorate.uuid, 'private-defense'),
            'private_defense_date': cls._format_date(doctorate.current_private_defense.datetime),
            'private_defense_place': doctorate.current_private_defense.place,
            'reference': doctorate.reference,
            'sender_name': f'{sender_first_name} {sender_last_name}',
            'management_entity_name': doctorate.management_entity_title,  # From annotation
        }

    @classmethod
    def inviter_membres_jury(cls, parcours_doctoral: ParcoursDoctoral, auteur: PersonneConnueUclDTO) -> None:
        doctorate = cls.get_doctorate(doctorate_uuid=parcours_doctoral.entity_id.uuid)

        common_tokens = cls.get_common_tokens(
            doctorate=doctorate,
            sender_first_name=auteur.prenom,
            sender_last_name=auteur.nom,
        )

        email_templates = get_email_templates_by_language(
            identifier=PARCOURS_DOCTORAL_EMAIL_PRIVATE_DEFENSE_JURY_INVITATION,
            management_entity_id=doctorate.training.management_entity_id,
        )

        jury_members = JuryMember.objects.filter(parcours_doctoral=doctorate).select_related(
            'promoter__person',
            'person',
        )

        for jury_member in jury_members:
            jury_member_info = cls.get_jury_member_info(jury_member=jury_member)

            current_language = jury_member_info['language'] or settings.LANGUAGE_CODE

            tokens = {
                **common_tokens,
                'jury_member_first_name': jury_member_info['first_name'],
                'jury_member_last_name': jury_member_info['last_name'],
            }

            email_template = email_templates[current_language]

            with override(current_language):
                email_notification = EmailNotification(
                    recipient=jury_member_info['person'] or jury_member_info['email'],
                    subject=email_template.render_subject(tokens),
                    html_content=email_template.body_as_html(tokens),
                    plain_text_content=email_template.body_as_plain(tokens),
                )

            jury_member_email_message = EmailNotificationHandler.build(email_notification)
            EmailNotificationHandler.create(jury_member_email_message, person=jury_member_info['person'])
