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

from typing import Union

from django.conf import settings
from django.utils.translation import gettext as _
from osis_mail_template.utils import generate_email, transform_html_to_text
from osis_notification.contrib.handlers import EmailNotificationHandler
from osis_notification.contrib.notification import EmailNotification

from parcours_doctoral.ddd.domain.model.enums import (
    ChoixStatutParcoursDoctoral,
    ChoixTypeFinancement,
)
from parcours_doctoral.ddd.epreuve_confirmation.domain.model.epreuve_confirmation import (
    EpreuveConfirmation,
)
from parcours_doctoral.ddd.epreuve_confirmation.domain.service.i_notification import (
    INotification,
)
from parcours_doctoral.ddd.epreuve_confirmation.dtos import EpreuveConfirmationDTO
from parcours_doctoral.infrastructure.mixins.notification import NotificationMixin
from parcours_doctoral.mail_templates.confirmation_paper import (
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRE,
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRI,
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRE,
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRI,
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRE,
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRI,
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_STUDENT,
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_SUBMISSION_ADRE,
)
from parcours_doctoral.models import ParcoursDoctoral as ParcoursDoctoralModel
from parcours_doctoral.models.task import ParcoursDoctoralTask
from parcours_doctoral.utils.url import (
    get_parcours_doctoral_link_back,
    get_parcours_doctoral_link_front,
)


class Notification(NotificationMixin, INotification):
    @classmethod
    def _get_doctorate(cls, doctorate_uuid):
        return ParcoursDoctoralModel.objects.select_related(
            'international_scholarship',
            'student',
            'training',
        ).get(uuid=doctorate_uuid)

    @classmethod
    def get_common_tokens(
        cls,
        parcours_doctoral: ParcoursDoctoralModel,
        confirmation_paper: Union[EpreuveConfirmationDTO, EpreuveConfirmation],
    ) -> dict:
        """Return common tokens about a parcours doctoral"""
        financing_type = (
            (
                str(parcours_doctoral.international_scholarship)
                if parcours_doctoral.international_scholarship_id
                else parcours_doctoral.other_international_scholarship
            )
            if parcours_doctoral.financing_type == ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name
            else ChoixTypeFinancement.get_value(parcours_doctoral.financing_type)
        )

        return {
            "student_first_name": parcours_doctoral.student.first_name,
            "student_last_name": parcours_doctoral.student.last_name,
            "training_title": cls._get_parcours_doctoral_title_translation(parcours_doctoral),
            "parcours_doctoral_link_front": get_parcours_doctoral_link_front(parcours_doctoral.uuid),
            "parcours_doctoral_link_back": get_parcours_doctoral_link_back(parcours_doctoral.uuid),
            "confirmation_paper_link_front": get_parcours_doctoral_link_front(parcours_doctoral.uuid, 'confirmation'),
            "confirmation_paper_link_back": get_parcours_doctoral_link_back(parcours_doctoral.uuid, 'confirmation'),
            "confirmation_paper_date": cls._format_date(confirmation_paper.date),
            "confirmation_paper_deadline": cls._format_date(confirmation_paper.date_limite),
            "scholarship_grant_acronym": financing_type,
            "extension_request_proposed_date": (
                cls._format_date(confirmation_paper.demande_prolongation.nouvelle_echeance)
                if confirmation_paper.demande_prolongation
                else ''
            ),
        }

    @classmethod
    def notifier_soumission(cls, epreuve_confirmation: EpreuveConfirmation) -> None:
        parcours_doctoral = cls._get_doctorate(doctorate_uuid=epreuve_confirmation.parcours_doctoral_id.uuid)
        common_tokens = cls.get_common_tokens(parcours_doctoral, epreuve_confirmation)

        if parcours_doctoral.status == ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name:
            # Already submitted at least once
            manager_notification_content = _(
                '<a href="%(confirmation_paper_link_back)s">PhD</a> - '
                '%(student_first_name)s %(student_last_name)s submitted new data '
                'for the confirmation paper for %(training_title)s'
            )

        else:
            # First submission
            manager_notification_content = _(
                '<a href="%(confirmation_paper_link_back)s">PhD</a> - '
                '%(student_first_name)s %(student_last_name)s submitted data '
                'for the first time for the confirmation paper for %(training_title)s'
            )

            # Notify ADRE : email
            email_message = generate_email(
                PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_SUBMISSION_ADRE,
                settings.LANGUAGE_CODE,
                common_tokens,
                recipients=[cls.ADRE_EMAIL],
            )
            EmailNotificationHandler.create(email_message, person=None)

        # Notify the CDD managers > web notification
        cls._send_notification_to_managers(
            education_group_id=parcours_doctoral.training.education_group_id,
            content=manager_notification_content,
            tokens=common_tokens,
        )

    @classmethod
    def notifier_completion_par_promoteur(cls, epreuve_confirmation: EpreuveConfirmation) -> None:
        parcours_doctoral = cls._get_doctorate(doctorate_uuid=epreuve_confirmation.parcours_doctoral_id.uuid)
        common_tokens = cls.get_common_tokens(parcours_doctoral, epreuve_confirmation)

        # Notify the CDD managers > web notification
        cls._send_notification_to_managers(
            education_group_id=parcours_doctoral.training.education_group_id,
            content=_(
                '<a href="%(confirmation_paper_link_back)s">PhD</a> - '
                'A supervisor submitted documents related to the confirmation paper of '
                '%(student_first_name)s %(student_last_name)s for %(training_title)s'
            ),
            tokens=common_tokens,
        )

    @classmethod
    def notifier_nouvelle_echeance(cls, epreuve_confirmation: EpreuveConfirmation) -> None:
        parcours_doctoral = cls._get_doctorate(doctorate_uuid=epreuve_confirmation.parcours_doctoral_id.uuid)
        common_tokens = cls.get_common_tokens(parcours_doctoral, epreuve_confirmation)

        # Notify the CCD managers > web notification
        cls._send_notification_to_managers(
            education_group_id=parcours_doctoral.training.education_group_id,
            content=_(
                '<a href="%(confirmation_paper_link_back)s">PhD</a> - '
                '%(student_first_name)s %(student_last_name)s proposed a new deadline '
                '(%(extension_request_proposed_date)s) for the confirmation paper for %(training_title)s'
            ),
            tokens=common_tokens,
        )

    @classmethod
    def notifier_echec_epreuve(
        cls,
        epreuve_confirmation: EpreuveConfirmation,
        sujet_notification_candidat: str,
        message_notification_candidat: str,
    ) -> None:
        parcours_doctoral = cls._get_doctorate(doctorate_uuid=epreuve_confirmation.parcours_doctoral_id.uuid)

        email_notification = EmailNotification(
            recipient=parcours_doctoral.student,
            subject=sujet_notification_candidat,
            html_content=message_notification_candidat,
            plain_text_content=transform_html_to_text(message_notification_candidat),
        )

        student_email_message = EmailNotificationHandler.build(email_notification)
        student_email_message['Cc'] = cls._get_supervision_actor_email_cc(parcours_doctoral)

        EmailNotificationHandler.create(student_email_message, person=parcours_doctoral.student)

        common_tokens = cls.get_common_tokens(parcours_doctoral, epreuve_confirmation)

        # Notify ADRE > email
        adre_email_message = generate_email(
            PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRE,
            settings.LANGUAGE_CODE,
            common_tokens,
            recipients=[cls.ADRE_EMAIL],
        )
        EmailNotificationHandler.create(adre_email_message, person=None)

        # Notify ADRI > email
        adri_email_message = generate_email(
            PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRI,
            settings.LANGUAGE_CODE,
            common_tokens,
            recipients=[cls.ADRI_EMAIL],
        )
        EmailNotificationHandler.create(adri_email_message, person=None)

    @classmethod
    def notifier_repassage_epreuve(
        cls,
        epreuve_confirmation: EpreuveConfirmation,
        sujet_notification_candidat: str,
        message_notification_candidat: str,
    ) -> None:
        parcours_doctoral = cls._get_doctorate(doctorate_uuid=epreuve_confirmation.parcours_doctoral_id.uuid)

        email_notification = EmailNotification(
            recipient=parcours_doctoral.student,
            subject=sujet_notification_candidat,
            html_content=message_notification_candidat,
            plain_text_content=transform_html_to_text(message_notification_candidat),
        )

        # Notify the promoters and the ca members > email (cc)
        email_message = EmailNotificationHandler.build(email_notification)
        email_message['Cc'] = cls._get_supervision_actor_email_cc(parcours_doctoral)

        EmailNotificationHandler.create(email_message, person=parcours_doctoral.student)

        common_tokens = cls.get_common_tokens(parcours_doctoral, epreuve_confirmation)

        # Notify ADRE > email
        adre_email_message = generate_email(
            PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRE,
            settings.LANGUAGE_CODE,
            common_tokens,
            recipients=[cls.ADRE_EMAIL],
        )
        EmailNotificationHandler.create(adre_email_message, person=None)

        # Notify ADRI > email
        adri_email_message = generate_email(
            PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRI,
            settings.LANGUAGE_CODE,
            common_tokens,
            recipients=[cls.ADRI_EMAIL],
        )
        EmailNotificationHandler.create(adri_email_message, person=None)

    @classmethod
    def notifier_reussite_epreuve(cls, epreuve_confirmation: EpreuveConfirmation):
        parcours_doctoral = cls._get_doctorate(doctorate_uuid=epreuve_confirmation.parcours_doctoral_id.uuid)

        # Create the async task to generate the success attestation
        cls._create_async_task(
            task_name=_('Create the confirmation paper success attestation'),
            task_description=_('Create the confirmation paper success attestation as PDF'),
            task_type=ParcoursDoctoralTask.TaskType.CONFIRMATION_SUCCESS_ATTESTATION,
            parcours_doctoral=parcours_doctoral,
            person=parcours_doctoral.student,
        )

        common_tokens = cls.get_common_tokens(parcours_doctoral, epreuve_confirmation)

        # Notify the student > email
        student_email_message = generate_email(
            PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_STUDENT,
            parcours_doctoral.student.language,
            common_tokens,
            recipients=[parcours_doctoral.student.email],
        )
        EmailNotificationHandler.create(student_email_message, person=parcours_doctoral.student)

        # Notify ADRE > email
        adre_email_message = generate_email(
            PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRE,
            settings.LANGUAGE_CODE,
            common_tokens,
            recipients=[cls.ADRE_EMAIL],
        )
        EmailNotificationHandler.create(adre_email_message, person=None)

        # Notify ADRI > email
        adri_email_message = generate_email(
            PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRI,
            settings.LANGUAGE_CODE,
            common_tokens,
            recipients=[cls.ADRI_EMAIL],
        )
        EmailNotificationHandler.create(adri_email_message, person=None)
