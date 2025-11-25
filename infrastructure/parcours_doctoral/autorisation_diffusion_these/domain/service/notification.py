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
from django.db.models import Prefetch
from django.utils.translation import pgettext_lazy
from osis_mail_template import generate_email
from osis_notification.contrib.handlers import EmailNotificationHandler
from osis_signature.models import Actor

from parcours_doctoral.auth.roles.sceb_manager import ScebManager
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.autorisation_diffusion_these import (
    AutorisationDiffusionThese,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.enums import (
    RoleActeur,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.service.i_notification import (
    INotification,
)
from parcours_doctoral.infrastructure.mixins.notification import NotificationMixin
from parcours_doctoral.mail_templates.thesis_distribution_authorization import (
    PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_ADRE_APPROVAL,
    PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_ADRE_REFUSAL,
    PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_PROMOTER_APPROVAL,
    PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_PROMOTER_INVITATION,
    PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_PROMOTER_INVITATION_CONFIRMATION,
    PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_PROMOTER_REFUSAL,
)
from parcours_doctoral.models import ParcoursDoctoral
from parcours_doctoral.models.thesis_distribution_authorization import (
    ThesisDistributionAuthorizationActor,
)
from parcours_doctoral.utils.url import (
    get_parcours_doctoral_link_back,
    get_parcours_doctoral_link_front,
)


class Notification(NotificationMixin, INotification):
    @classmethod
    def get_doctorate(cls, doctorate_uuid) -> ParcoursDoctoral:
        """Return the doctorate"""
        doctorate: ParcoursDoctoral = (
            ParcoursDoctoral.objects.select_related(
                'student',
                'training',
                'thesis_distribution_authorization',
            )
            .annotate_training_management_entity_title()
            .get(uuid=doctorate_uuid)
        )

        signature_actors = ThesisDistributionAuthorizationActor.objects.filter(
            process_id=doctorate.thesis_distribution_authorization.signature_group_id,
        ).select_related('person')

        setattr(doctorate, 'loaded_actors_by_role', {actor.role: actor for actor in signature_actors})

        return doctorate

    @classmethod
    def get_common_tokens(
        cls,
        doctorate: ParcoursDoctoral,
    ) -> dict:
        """Return common tokens about a doctorate"""
        tokens = {
            'training_title': cls._get_parcours_doctoral_title_translation(doctorate),
            'parcours_doctoral_link_front': get_parcours_doctoral_link_front(doctorate.uuid),
            'parcours_doctoral_link_back': get_parcours_doctoral_link_back(doctorate.uuid),
            'student_first_name': doctorate.student.first_name,
            'student_last_name': doctorate.student.last_name,
            'thesis_distribution_authorization_form_front_link': get_parcours_doctoral_link_front(
                doctorate.uuid,
                'authorization-distribution',
            ),
            'thesis_distribution_authorization_form_back_link': get_parcours_doctoral_link_back(
                doctorate.uuid,
                'authorization-distribution',
            ),
            'promoter_name': '',
            'promoter_title_uppercase': '',
            'promoter_title_lowercase': '',
            'promoter_refusal_reason': '',
            'cdd_manager_names': cls._get_program_managers_names(doctorate.training.education_group_id),
            'doctoral_commission': doctorate.management_entity_title,
            'adre_manager_name': '',
            'adre_refusal_reason': '',
            'sceb_manager_name': '',
            'sceb_refusal_reason': '',
            'dial_link': 'A_IMPLEMENTER',
        }

        promoter = doctorate.loaded_actors_by_role.get(RoleActeur.PROMOTEUR.name)
        if promoter:
            tokens['promoter_name'] = cls._format_actor(promoter)
            tokens['promoter_title_uppercase'] = {
                'F': pgettext_lazy('female gender', 'Professor'),
                'H': pgettext_lazy('male gender', 'Professor'),
            }.get(promoter.person.gender) or pgettext_lazy('other gender', 'Professor')
            tokens['promoter_title_lowercase'] = tokens['promoter_title_uppercase'].lower()
            tokens['promoter_refusal_reason'] = promoter.rejection_reason

        adre_manager = doctorate.loaded_actors_by_role.get(RoleActeur.ADRE.name)
        if adre_manager:
            tokens['adre_manager_name'] = cls._format_actor(adre_manager)
            tokens['adre_refusal_reason'] = adre_manager.rejection_reason

        sceb_manager = doctorate.loaded_actors_by_role.get(RoleActeur.SCEB.name)
        if sceb_manager:
            tokens['sceb_manager_name'] = cls._format_actor(sceb_manager)
            tokens['sceb_refusal_reason'] = sceb_manager.rejection_reason

        return tokens

    @classmethod
    def _format_actor(cls, actor: Actor | None):
        """Format the name of the actor"""
        if not actor:
            return ''

        return f'{actor.first_name} {actor.last_name}'

    @classmethod
    def inviter_promoteur_reference(cls, autorisation_diffusion_these: AutorisationDiffusionThese) -> None:
        doctorate = cls.get_doctorate(doctorate_uuid=autorisation_diffusion_these.entity_id.uuid)

        tokens = cls.get_common_tokens(doctorate=doctorate)

        # Mail sent to the promoter
        promoter = doctorate.loaded_actors_by_role.get(RoleActeur.PROMOTEUR.name)
        email_message = generate_email(
            PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_PROMOTER_INVITATION,
            promoter.person.language or settings.LANGUAGE_CODE,
            tokens,
            recipients=[promoter.person.email],
        )

        EmailNotificationHandler.create(email_message, person=promoter.person)

        # Mail sent to the student
        sceb_managers = ScebManager.objects.all().select_related('person')
        cc_list = [cls._format_email(sceb_manager.person) for sceb_manager in sceb_managers]

        email_message = generate_email(
            PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_PROMOTER_INVITATION_CONFIRMATION,
            doctorate.student.language or settings.LANGUAGE_CODE,
            tokens,
            recipients=[doctorate.student.email],
            cc_recipients=cc_list,
        )

        EmailNotificationHandler.create(email_message, person=doctorate.student)

    @classmethod
    def refuser_these_par_promoteur_reference(cls, autorisation_diffusion_these: AutorisationDiffusionThese) -> None:
        doctorate = cls.get_doctorate(doctorate_uuid=autorisation_diffusion_these.entity_id.uuid)

        tokens = cls.get_common_tokens(doctorate=doctorate)

        # Mail sent to the student
        email_message = generate_email(
            PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_PROMOTER_REFUSAL,
            doctorate.student.language or settings.LANGUAGE_CODE,
            tokens,
            recipients=[doctorate.student.email],
        )

        EmailNotificationHandler.create(email_message, person=doctorate.student)

    @classmethod
    def accepter_these_par_promoteur_reference(cls, autorisation_diffusion_these: AutorisationDiffusionThese) -> None:
        doctorate = cls.get_doctorate(doctorate_uuid=autorisation_diffusion_these.entity_id.uuid)

        tokens = cls.get_common_tokens(doctorate=doctorate)
        adre_manager = doctorate.loaded_actors_by_role.get(RoleActeur.ADRE.name)

        # Mail sent to the adre manager
        email_message = generate_email(
            PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_PROMOTER_APPROVAL,
            adre_manager.person.language or settings.LANGUAGE_CODE,
            tokens,
            recipients=[adre_manager.person.email],
        )

        EmailNotificationHandler.create(email_message, person=adre_manager.person)

    @classmethod
    def refuser_these_par_adre(cls, autorisation_diffusion_these: AutorisationDiffusionThese) -> None:
        doctorate = cls.get_doctorate(doctorate_uuid=autorisation_diffusion_these.entity_id.uuid)

        promoter = doctorate.loaded_actors_by_role.get(RoleActeur.PROMOTEUR.name)

        tokens = cls.get_common_tokens(doctorate=doctorate)

        # Mail sent to the student
        email_message = generate_email(
            PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_ADRE_REFUSAL,
            doctorate.student.language or settings.LANGUAGE_CODE,
            tokens,
            recipients=[doctorate.student.email],
            cc_recipients=[promoter.person.email],
        )

        EmailNotificationHandler.create(email_message, person=doctorate.student)

    @classmethod
    def accepter_these_par_adre(cls, autorisation_diffusion_these: AutorisationDiffusionThese) -> None:
        doctorate = cls.get_doctorate(doctorate_uuid=autorisation_diffusion_these.entity_id.uuid)

        tokens = cls.get_common_tokens(doctorate=doctorate)
        sceb_manager = doctorate.loaded_actors_by_role.get(RoleActeur.SCEB.name)

        # Mail sent to the sceb manager
        email_message = generate_email(
            PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_ADRE_APPROVAL,
            sceb_manager.person.language or settings.LANGUAGE_CODE,
            tokens,
            recipients=[sceb_manager.person.email],
        )

        EmailNotificationHandler.create(email_message, person=sceb_manager.person)
