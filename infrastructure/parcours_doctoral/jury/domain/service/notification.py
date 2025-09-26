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

from django.conf import settings
from django.db.models import Value
from django.db.models.functions import Concat
from django.utils.functional import lazy
from django.utils.timezone import now
from django.utils.translation import get_language
from osis_mail_template.utils import generate_email
from osis_notification.contrib.handlers import EmailNotificationHandler
from osis_signature.enums import SignatureState
from osis_signature.utils import get_signing_token

from base.auth.roles.program_manager import ProgramManager
from base.models.entity_version import EntityVersion
from base.models.enums.mandate_type import MandateTypes
from base.models.mandatary import Mandatary
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoral
from parcours_doctoral.ddd.jury.domain.model.jury import Jury, MembreJury
from parcours_doctoral.ddd.jury.domain.service.i_notification import INotification
from parcours_doctoral.ddd.jury.dtos.jury import AvisDTO
from parcours_doctoral.mail_templates import (
    PARCOURS_DOCTORAL_JURY_EMAIL_SIGNATURE_REQUESTS_MEMBER,
    PARCOURS_DOCTORAL_JURY_EMAIL_SIGNATURE_REQUESTS_PROMOTER,
)
from parcours_doctoral.mail_templates.jury import (
    PARCOURS_DOCTORAL_JURY_EMAIL_ADRE_APPROVAL,
    PARCOURS_DOCTORAL_JURY_EMAIL_ADRE_REFUSAL,
    PARCOURS_DOCTORAL_JURY_EMAIL_CDD_APPROVAL,
    PARCOURS_DOCTORAL_JURY_EMAIL_CDD_REFUSAL,
    PARCOURS_DOCTORAL_JURY_EMAIL_MEMBER_REFUSAL,
)
from parcours_doctoral.models import JuryActor
from parcours_doctoral.models.parcours_doctoral import (
    ParcoursDoctoral as ParcoursDoctoralModel,
)
from parcours_doctoral.utils.url import (
    get_parcours_doctoral_link_back,
    get_parcours_doctoral_link_front,
)
from reference.services.mandates import MandateFunctionEnum, MandatesService

SSH_SECTOR_ACRONYM = 'SSH'


class Notification(INotification):
    @classmethod
    def get_common_tokens(cls, parcours_doctoral: ParcoursDoctoralModel):
        """Return common tokens about a submission"""
        return {
            "student_first_name": parcours_doctoral.student.first_name,
            "student_last_name": parcours_doctoral.student.last_name,
            "training_title": cls._get_parcours_doctoral_title_translation(parcours_doctoral),
            "parcours_doctoral_link_front_jury": get_parcours_doctoral_link_front(parcours_doctoral.uuid, tab='jury'),
            "parcours_doctoral_link_front": get_parcours_doctoral_link_front(parcours_doctoral.uuid),
            "parcours_doctoral_link_back": get_parcours_doctoral_link_back(parcours_doctoral.uuid),
            "cdd_manager_names": cls._get_program_managers_names(parcours_doctoral.training.education_group_id),
            "doctoral_commission": parcours_doctoral.training.management_entity.most_recent_entity_version.title,
        }

    @classmethod
    def _get_program_managers_names(cls, education_group_id):
        """
        Return the concatenation of the names of the program managers of the specified education group.
        :param education_group_id: The id of the education group
        :return: a string containing the names of the managers
        """
        return ', '.join(
            ProgramManager.objects.filter(education_group_id=education_group_id)
            .annotate(person_name=Concat('person__first_name', Value(' '), 'person__last_name'))
            .values_list('person_name', flat=True)
        )

    @classmethod
    def _get_adre_manager_name(cls):
        """
        Return the concatenation of the names of the adre managers.
        :return: a string containing the names of the managers
        """
        return ', '.join(
            Mandatary.objects.filter(
                mandate__function=MandateTypes.RECTOR.name,
                end_date__gt=now(),
            )
            .annotate(person_name=Concat('person__first_name', Value(' '), 'person__last_name'))
            .values_list('person_name', flat=True)
        )

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
    def _lien_invitation_externe(cls, parcours_doctoral, actor):
        return get_parcours_doctoral_link_front(
            uuid=parcours_doctoral.entity_id.uuid,
            tab='jury/external-approval/',
        ) + get_signing_token(actor)

    @classmethod
    def envoyer_signatures(cls, parcours_doctoral: ParcoursDoctoral, jury: Jury) -> None:
        parcours_doctoral_instance = ParcoursDoctoralModel.objects.get(uuid=parcours_doctoral.entity_id.uuid)

        # Tokens communs
        common_tokens = cls.get_common_tokens(parcours_doctoral_instance)
        common_tokens["parcours_doctoral_link_back"] = get_parcours_doctoral_link_back(
            uuid=parcours_doctoral_instance.uuid,
            tab='jury',
        )
        common_tokens["parcours_doctoral_link_front"] = get_parcours_doctoral_link_front(
            uuid=parcours_doctoral_instance.uuid,
            tab='jury',
        )

        # Envoyer aux acteurs n'ayant pas répondu
        actor_list = JuryActor.objects.filter(process=parcours_doctoral_instance.jury_group).select_related('person')
        actors_invited = [actor for actor in actor_list if actor.last_state == SignatureState.INVITED.name]
        for actor in actors_invited:
            tokens = {
                **common_tokens,
                "signataire_first_name": actor.first_name,
                "signataire_last_name": actor.last_name,
            }
            if actor.is_external:
                tokens["parcours_doctoral_link_front"] = cls._lien_invitation_externe(parcours_doctoral, actor)
            if actor.is_promoter:
                email_message = generate_email(
                    PARCOURS_DOCTORAL_JURY_EMAIL_SIGNATURE_REQUESTS_PROMOTER,
                    actor.language,
                    tokens,
                    recipients=[actor.email],
                )
            else:
                email_message = generate_email(
                    PARCOURS_DOCTORAL_JURY_EMAIL_SIGNATURE_REQUESTS_MEMBER,
                    actor.language,
                    tokens,
                    recipients=[actor.email],
                )
            EmailNotificationHandler.create(email_message, person=actor.person_id and actor.person)

    @classmethod
    def renvoyer_invitation(cls, parcours_doctoral: ParcoursDoctoral, membre: MembreJury) -> None:
        parcours_doctoral_instance = ParcoursDoctoralModel.objects.get(uuid=parcours_doctoral.entity_id.uuid)
        actor = JuryActor.objects.select_related('person').get(
            process=parcours_doctoral_instance.jury_group,
            uuid=membre.uuid,
        )

        if actor.is_external:
            # Réinitiliser l'état afin de mettre à jour le token
            actor.switch_state(SignatureState.INVITED)
            actor.refresh_from_db()

        tokens = {
            **cls.get_common_tokens(parcours_doctoral_instance),
            "signataire_first_name": actor.first_name,
            "signataire_last_name": actor.last_name,
            "parcours_doctoral_link_front": (
                cls._lien_invitation_externe(parcours_doctoral, actor)
                if actor.is_external
                else get_parcours_doctoral_link_front(
                    uuid=parcours_doctoral_instance.uuid,
                    tab='jury',
                )
            ),
        }

        if actor.is_promoter:
            email_message = generate_email(
                PARCOURS_DOCTORAL_JURY_EMAIL_SIGNATURE_REQUESTS_PROMOTER,
                actor.language,
                tokens,
                recipients=[actor.email],
            )
        else:
            email_message = generate_email(
                PARCOURS_DOCTORAL_JURY_EMAIL_SIGNATURE_REQUESTS_MEMBER,
                actor.language,
                tokens,
                recipients=[actor.email],
            )
        EmailNotificationHandler.create(email_message, person=actor.person_id and actor.person)

    @classmethod
    def notifier_refus(cls, parcours_doctoral: ParcoursDoctoral, signataire: MembreJury, avis: AvisDTO) -> None:
        parcours_doctoral_instance = ParcoursDoctoralModel.objects.get(uuid=parcours_doctoral.entity_id.uuid)

        # Tokens communs
        tokens = {
            **cls.get_common_tokens(parcours_doctoral_instance),
            "signataire_first_name": signataire.prenom,
            "signataire_last_name": signataire.nom,
            "refusal_reason": avis.motif_refus,
        }

        # Envoyer aux doctorant et promoteurs
        actor_list = JuryActor.objects.filter(process=parcours_doctoral_instance.jury_group).select_related('person')
        promoteurs = [actor for actor in actor_list if actor.is_promoter]
        email_message = generate_email(
            PARCOURS_DOCTORAL_JURY_EMAIL_MEMBER_REFUSAL,
            parcours_doctoral_instance.student.language,
            tokens,
            recipients=[parcours_doctoral_instance.student.private_email],
            cc_recipients=[actor.email for actor in promoteurs],
        )
        EmailNotificationHandler.create(email_message, person=parcours_doctoral_instance.student)

    @classmethod
    def notifier_approbation_cdd(
        cls, parcours_doctoral: ParcoursDoctoral, signataire: MembreJury, avis: AvisDTO
    ) -> None:
        parcours_doctoral_instance = ParcoursDoctoralModel.objects.get(uuid=parcours_doctoral.entity_id.uuid)

        # Tokens communs
        tokens = {
            **cls.get_common_tokens(parcours_doctoral_instance),
            "signataire_first_name": signataire.prenom,
            "signataire_last_name": signataire.nom,
        }

        # Envoyer aux gestionnaires ADRE et aux doyens pour les doctorats du secteur SSH
        gestionnaire_adre = Mandatary.objects.filter(
            mandate__function=MandateTypes.RECTOR.name,
            end_date__gt=now(),
        ).first()
        email_message = generate_email(
            PARCOURS_DOCTORAL_JURY_EMAIL_CDD_APPROVAL,
            parcours_doctoral_instance.student.language,
            tokens,
            recipients=[gestionnaire_adre.person.email],
        )
        EmailNotificationHandler.create(email_message, person=parcours_doctoral_instance.student)

    @classmethod
    def notifier_refus_cdd(cls, parcours_doctoral: ParcoursDoctoral, signataire: MembreJury, avis: AvisDTO) -> None:
        parcours_doctoral_instance = ParcoursDoctoralModel.objects.get(uuid=parcours_doctoral.entity_id.uuid)

        # Tokens communs
        tokens = {
            **cls.get_common_tokens(parcours_doctoral_instance),
            "signataire_first_name": signataire.prenom,
            "signataire_last_name": signataire.nom,
            "refusal_reason": avis.motif_refus,
        }

        # Envoyer au doctorant et promoteurs
        actor_list = JuryActor.objects.filter(process=parcours_doctoral_instance.jury_group).select_related('person')
        promoteurs = [actor for actor in actor_list if actor.is_promoter]
        email_message = generate_email(
            PARCOURS_DOCTORAL_JURY_EMAIL_CDD_REFUSAL,
            parcours_doctoral_instance.student.language,
            tokens,
            recipients=[parcours_doctoral_instance.student.private_email],
            cc_recipients=[actor.email for actor in promoteurs],
        )
        EmailNotificationHandler.create(email_message, person=parcours_doctoral_instance.student)

    @classmethod
    def notifier_approbation_adre(
        cls, parcours_doctoral: ParcoursDoctoral, signataire: MembreJury, avis: AvisDTO
    ) -> None:
        parcours_doctoral_instance = ParcoursDoctoralModel.objects.get(uuid=parcours_doctoral.entity_id.uuid)

        # Tokens communs
        tokens = {
            **cls.get_common_tokens(parcours_doctoral_instance),
            "adre_manager_name": cls._get_adre_manager_name(),
            "signataire_first_name": signataire.prenom,
            "signataire_last_name": signataire.nom,
        }

        # Envoyer au doctorant et promoteurs
        actor_list = JuryActor.objects.filter(process=parcours_doctoral_instance.jury_group).select_related('person')
        promoteurs = [actor for actor in actor_list if actor.is_promoter]
        cc_recipients = [actor.email for actor in promoteurs]
        # Ajouter les doyens pour le secteur SSH
        parcours_doctoral = (
            ParcoursDoctoralModel.objects.annotate_faculte_formation()
            .annotate_secteur_formation()
            .get(uuid=parcours_doctoral.entity_id.uuid)
        )
        if parcours_doctoral.sigle_secteur_formation == SSH_SECTOR_ACRONYM:
            doyens = MandatesService.get(
                function=MandateFunctionEnum.DOYEN,
                entity_acronym=parcours_doctoral.sigle_faculte_formation,
            )
            today = datetime.date.today()
            for doyen in doyens:
                if doyen['date_end'] is None or datetime.date(*doyen['date_end'].split('/') > today):
                    cc_recipients.append(doyen['email'])
        email_message = generate_email(
            PARCOURS_DOCTORAL_JURY_EMAIL_ADRE_APPROVAL,
            parcours_doctoral_instance.student.language,
            tokens,
            recipients=[parcours_doctoral_instance.student.private_email],
            cc_recipients=cc_recipients,
        )
        EmailNotificationHandler.create(email_message, person=parcours_doctoral_instance.student)

    @classmethod
    def notifier_refus_adre(cls, parcours_doctoral: ParcoursDoctoral, signataire: MembreJury, avis: AvisDTO) -> None:
        parcours_doctoral_instance = ParcoursDoctoralModel.objects.get(uuid=parcours_doctoral.entity_id.uuid)

        # Tokens communs
        tokens = {
            **cls.get_common_tokens(parcours_doctoral_instance),
            "adre_manager_name": cls._get_adre_manager_name(),
            "signataire_first_name": signataire.prenom,
            "signataire_last_name": signataire.nom,
            "refusal_reason": avis.motif_refus,
        }

        # Envoyer au doctorant et promoteurs
        actor_list = JuryActor.objects.filter(process=parcours_doctoral_instance.jury_group).select_related('person')
        promoteurs = [actor for actor in actor_list if actor.is_promoter]
        email_message = generate_email(
            PARCOURS_DOCTORAL_JURY_EMAIL_ADRE_REFUSAL,
            parcours_doctoral_instance.student.language,
            tokens,
            recipients=[parcours_doctoral_instance.student.private_email],
            cc_recipients=[actor.email for actor in promoteurs],
        )
        EmailNotificationHandler.create(email_message, person=parcours_doctoral_instance.student)
