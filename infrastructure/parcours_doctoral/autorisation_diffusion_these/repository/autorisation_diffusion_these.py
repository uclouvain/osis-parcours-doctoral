# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################

from django.db import transaction
from django.db.models import QuerySet
from osis_signature.models import Actor, Process, StateHistory

from base.models.person import Person
from parcours_doctoral.constants import INSTITUTION_UCL
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.autorisation_diffusion_these import (
    AutorisationDiffusionThese,
    AutorisationDiffusionTheseIdentity,
    SignataireAutorisationDiffusionThese,
    SignataireAutorisationDiffusionTheseIdentity,
    SignatureAutorisationDiffusionThese,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.enums import (
    ChoixEtatSignature,
    ChoixStatutAutorisationDiffusionThese,
    RoleActeur,
    TypeModalitesDiffusionThese,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.validator.exceptions import (
    AutorisationDiffusionTheseNonTrouveException,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.dtos.autorisation_diffusion_these import (
    AutorisationDiffusionTheseDTO,
    SignataireAutorisationDiffusionTheseDTO,
    SignatureAutorisationDiffusionTheseDTO,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.repository.i_autorisation_diffusion_these import (
    IAutorisationDiffusionTheseRepository,
)
from parcours_doctoral.models import ParcoursDoctoral
from parcours_doctoral.models.thesis_distribution_authorization import (
    ThesisDistributionAuthorization,
    ThesisDistributionAuthorizationActor,
)
from reference.models.language import Language


class AutorisationDiffusionTheseRepository(IAutorisationDiffusionTheseRepository):
    @classmethod
    def _get(cls, entity_id: AutorisationDiffusionTheseIdentity) -> ThesisDistributionAuthorization:
        try:
            doctorate = ParcoursDoctoral.objects.select_related(
                'thesis_distribution_authorization',
                'thesis_language',
            ).get(uuid=entity_id.uuid)
        except ParcoursDoctoral.DoesNotExist:
            raise AutorisationDiffusionTheseNonTrouveException

        if hasattr(doctorate, 'thesis_distribution_authorization'):
            return doctorate.thesis_distribution_authorization

        return ThesisDistributionAuthorization(parcours_doctoral=doctorate)

    @classmethod
    def _get_actors(cls, process_id) -> QuerySet[ThesisDistributionAuthorizationActor]:
        if not process_id:
            return ThesisDistributionAuthorizationActor.objects.none()
        return ThesisDistributionAuthorizationActor.objects.filter(process_id=process_id).select_related('person')

    @classmethod
    def get_dto(cls, entity_id: 'AutorisationDiffusionTheseIdentity') -> 'AutorisationDiffusionTheseDTO':
        db_object = cls._get(entity_id=entity_id)
        db_actors_objects = cls._get_actors(process_id=db_object.signature_group_id)

        return AutorisationDiffusionTheseDTO(
            uuid=str(entity_id.uuid),
            statut=db_object.status,
            sources_financement=db_object.funding_sources,
            resume_anglais=db_object.thesis_summary_in_english,
            resume_autre_langue=db_object.thesis_summary_in_other_language,
            mots_cles=db_object.thesis_keywords,
            type_modalites_diffusion=db_object.conditions,
            date_embargo=db_object.embargo_date,
            limitations_additionnelles_chapitres=db_object.additional_limitation_for_specific_chapters,
            modalites_diffusion_acceptees_le=db_object.accepted_on,
            signataires=(
                [
                    SignataireAutorisationDiffusionTheseDTO(
                        matricule=actor.person.global_id,
                        prenom=actor.person.first_name,
                        nom=actor.person.last_name,
                        email=actor.person.email,
                        genre=actor.person.gender,
                        role=actor.role,
                        institution=INSTITUTION_UCL,
                        uuid=str(actor.uuid),
                        signature=SignatureAutorisationDiffusionTheseDTO(
                            etat=actor.last_state,
                            date_heure=actor.last_state_date,
                            commentaire_externe=actor.comment,
                            commentaire_interne=actor.internal_comment,
                            motif_refus=actor.rejection_reason,
                        ),
                    )
                    for actor in db_actors_objects
                ]
            ),
        )

    @classmethod
    def get(cls, entity_id: 'AutorisationDiffusionTheseIdentity') -> 'AutorisationDiffusionThese':
        db_object = cls._get(entity_id=entity_id)
        db_actors_objects = cls._get_actors(process_id=db_object.signature_group_id)

        return AutorisationDiffusionThese(
            entity_id=entity_id,
            statut=ChoixStatutAutorisationDiffusionThese[db_object.status],
            sources_financement=db_object.funding_sources,
            resume_anglais=db_object.thesis_summary_in_english,
            resume_autre_langue=db_object.thesis_summary_in_other_language,
            langue_redaction_these=(
                db_object.parcours_doctoral.thesis_language.code if db_object.parcours_doctoral.thesis_language else ''
            ),
            mots_cles=db_object.thesis_keywords,
            type_modalites_diffusion=(
                TypeModalitesDiffusionThese[db_object.conditions] if db_object.conditions else None
            ),
            date_embargo=db_object.embargo_date,
            limitations_additionnelles_chapitres=db_object.additional_limitation_for_specific_chapters,
            modalites_diffusion_acceptees=db_object.acceptation_content,
            modalites_diffusion_acceptees_le=db_object.accepted_on,
            signataires=(
                {
                    RoleActeur[actor.role]: SignataireAutorisationDiffusionThese(
                        SignataireAutorisationDiffusionTheseIdentity(
                            matricule=actor.person.global_id,
                            role=RoleActeur[actor.role],
                        ),
                        signature=SignatureAutorisationDiffusionThese(
                            etat=ChoixEtatSignature[actor.last_state],
                            commentaire_externe=actor.comment,
                            commentaire_interne=actor.internal_comment,
                            motif_refus=actor.rejection_reason,
                        ),
                    )
                    for actor in db_actors_objects
                }
            ),
        )

    @classmethod
    @transaction.atomic
    def save(cls, entity: 'AutorisationDiffusionThese') -> 'AutorisationDiffusionTheseIdentity':
        db_object = cls._get(entity.entity_id)

        # Update doctorate data
        language_id: int | None = None
        if entity.langue_redaction_these:
            language_id = Language.objects.values_list('pk', flat=True).get(code=entity.langue_redaction_these)

        db_object.parcours_doctoral.thesis_language_id = language_id
        db_object.parcours_doctoral.save(update_fields=['thesis_language'])

        # Update authorization distribution thesis data
        db_object.status = entity.statut.name
        db_object.funding_sources = entity.sources_financement
        db_object.thesis_summary_in_english = entity.resume_anglais
        db_object.thesis_summary_in_other_language = entity.resume_autre_langue
        db_object.thesis_keywords = entity.mots_cles
        db_object.conditions = entity.type_modalites_diffusion.name if entity.type_modalites_diffusion else ''
        db_object.embargo_date = entity.date_embargo
        db_object.additional_limitation_for_specific_chapters = entity.limitations_additionnelles_chapitres
        db_object.accepted_on = entity.modalites_diffusion_acceptees_le
        db_object.acceptation_content = entity.modalites_diffusion_acceptees

        # Update the signatures
        existing_db_actors: dict[
            SignataireAutorisationDiffusionTheseIdentity,
            ThesisDistributionAuthorizationActor,
        ] = {}
        persons_by_global_id: dict[str, Person] = {}

        if db_object.signature_group_id:
            db_actors_objects = cls._get_actors(process_id=db_object.signature_group_id)
            for db_actor in db_actors_objects:
                existing_db_actors[
                    SignataireAutorisationDiffusionTheseIdentity(
                        matricule=db_actor.person.global_id,
                        role=RoleActeur[db_actor.role],
                    )
                ] = db_actor
                persons_by_global_id[db_actor.person.global_id] = db_actor.person

        else:
            # Initialize group if needed
            db_object.signature_group = Process.objects.create()

        db_object.save()

        # Retrieve the new persons related to new actors
        new_persons_to_fetch = [
            actor.entity_id.matricule
            for actor in entity.signataires.values()
            if actor.entity_id.matricule not in persons_by_global_id
        ]
        if new_persons_to_fetch:
            for person in Person.objects.filter(global_id__in=new_persons_to_fetch):
                persons_by_global_id[person.global_id] = person

        state_histories: list[StateHistory] = []

        # Create or update the existing actors
        for actor in entity.signataires.values():
            db_actor = existing_db_actors.pop(actor.entity_id, None) or ThesisDistributionAuthorizationActor(
                process_id=db_object.signature_group_id,
                role=actor.entity_id.role.name,
                person=persons_by_global_id[actor.entity_id.matricule],
            )

            # Only update the decision fields if it's a decision state
            if actor.signature.etat.name in {ChoixEtatSignature.APPROVED.name, ChoixEtatSignature.DECLINED.name}:
                db_actor.comment = actor.signature.commentaire_externe
                db_actor.internal_comment = actor.signature.commentaire_interne
                db_actor.rejection_reason = actor.signature.motif_refus

            # Create a new state if it has been updated
            if getattr(db_actor, 'last_state', None) != actor.signature.etat.name:
                state_histories.append(StateHistory(state=actor.signature.etat.name, actor=db_actor))

            db_actor.save()

        # Remove old members that are not used anymore
        if existing_db_actors:
            Actor.objects.filter(
                process_id=db_object.signature_group_id,
                uuid__in=[actor.uuid for actor in existing_db_actors.values()],
            ).delete()

        # Historize new states
        if state_histories:
            StateHistory.objects.bulk_create(state_histories)

        return entity.entity_id
