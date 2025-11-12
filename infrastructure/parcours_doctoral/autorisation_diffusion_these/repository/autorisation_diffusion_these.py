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
import uuid

from django.db import transaction
from django.db.models import Prefetch
from osis_signature.models import Actor, Process, StateHistory

from base.models.person import Person
from parcours_doctoral.constants import INSTITUTION_UCL
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.autorisation_diffusion_these import (
    AutorisationDiffusionThese,
    AutorisationDiffusionTheseIdentity,
    SignataireAutorisationDiffusionThese,
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
    ThesisDistributionAuthorizationActor,
)
from reference.models.language import Language


class AutorisationDiffusionTheseRepository(IAutorisationDiffusionTheseRepository):
    @classmethod
    def _get(cls, entity_id: AutorisationDiffusionTheseIdentity) -> ParcoursDoctoral:
        try:
            return (
                ParcoursDoctoral.objects.only(
                    'uuid',
                    'thesis_language',
                    'thesis_proposed_title',
                    'thesis_distribution_authorization_status',
                    'funding_sources',
                    'thesis_summary_in_english',
                    'thesis_summary_in_other_language',
                    'thesis_keywords',
                    'thesis_distribution_conditions',
                    'thesis_distribution_embargo_date',
                    'thesis_distribution_additional_limitation_for_specific_chapters',
                    'thesis_distribution_accepted_on',
                    'thesis_distribution_acceptation_content',
                    'thesis_distribution_authorization_group',
                )
                .select_related(
                    'thesis_language',
                    'thesis_distribution_authorization_group',
                )
                .prefetch_related(
                    Prefetch(
                        'thesis_distribution_authorization_group__actors',
                        queryset=Actor.objects.select_related('thesisdistributionauthorizationactor', 'person'),
                        to_attr='loaded_actors',
                    )
                )
                .get(uuid=entity_id.uuid)
            )
        except ParcoursDoctoral.DoesNotExist:
            raise AutorisationDiffusionTheseNonTrouveException

    @classmethod
    def get_dto(cls, entity_id: 'AutorisationDiffusionTheseIdentity') -> 'AutorisationDiffusionTheseDTO':
        db_object = cls._get(entity_id=entity_id)
        return AutorisationDiffusionTheseDTO(
            uuid=str(db_object.uuid),
            statut=db_object.thesis_distribution_authorization_status,
            sources_financement=db_object.funding_sources,
            resume_anglais=db_object.thesis_summary_in_english,
            resume_autre_langue=db_object.thesis_summary_in_other_language,
            mots_cles=db_object.thesis_keywords,
            type_modalites_diffusion=db_object.thesis_distribution_conditions,
            date_embargo=db_object.thesis_distribution_embargo_date,
            limitations_additionnelles_chapitres=(
                db_object.thesis_distribution_additional_limitation_for_specific_chapters
            ),
            modalites_diffusion_acceptees_le=db_object.thesis_distribution_accepted_on,
            signataires=(
                [
                    SignataireAutorisationDiffusionTheseDTO(
                        matricule=actor.person.global_id,
                        prenom=actor.person.first_name,
                        nom=actor.person.last_name,
                        email=actor.person.email,
                        genre=actor.person.gender,
                        role=actor.thesisdistributionauthorizationactor.role,
                        institution=INSTITUTION_UCL,
                        uuid=str(actor.uuid),
                        signature=SignatureAutorisationDiffusionTheseDTO(
                            etat=actor.last_state,
                            date_heure=actor.last_state_date,
                            commentaire_externe=actor.comment,
                            commentaire_interne=actor.thesisdistributionauthorizationactor.internal_comment,
                            motif_refus=actor.thesisdistributionauthorizationactor.rejection_reason,
                        ),
                    )
                    for actor in db_object.thesis_distribution_authorization_group.loaded_actors
                ]
                if db_object.thesis_distribution_authorization_group
                else []
            ),
        )

    @classmethod
    def get(cls, entity_id: 'AutorisationDiffusionTheseIdentity') -> 'AutorisationDiffusionThese':
        db_object = cls._get(entity_id=entity_id)

        return AutorisationDiffusionThese(
            entity_id=AutorisationDiffusionTheseIdentity(uuid=db_object.uuid),
            statut=ChoixStatutAutorisationDiffusionThese[db_object.thesis_distribution_authorization_status],
            sources_financement=db_object.funding_sources,
            resume_anglais=db_object.thesis_summary_in_english,
            resume_autre_langue=db_object.thesis_summary_in_other_language,
            langue_redaction_these=db_object.thesis_language.code if db_object.thesis_language else '',
            mots_cles=db_object.thesis_keywords,
            type_modalites_diffusion=(
                TypeModalitesDiffusionThese[db_object.thesis_distribution_conditions]
                if db_object.thesis_distribution_conditions
                else None
            ),
            date_embargo=db_object.thesis_distribution_embargo_date,
            limitations_additionnelles_chapitres=(
                db_object.thesis_distribution_additional_limitation_for_specific_chapters
            ),
            modalites_diffusion_acceptees=db_object.thesis_distribution_acceptation_content,
            modalites_diffusion_acceptees_le=db_object.thesis_distribution_accepted_on,
            signataires=(
                {
                    RoleActeur[actor.thesisdistributionauthorizationactor.role]: SignataireAutorisationDiffusionThese(
                        matricule=actor.person.global_id,
                        role=RoleActeur[actor.thesisdistributionauthorizationactor.role],
                        uuid=actor.uuid,
                        signature=SignatureAutorisationDiffusionThese(
                            etat=ChoixEtatSignature[actor.last_state],
                            commentaire_externe=actor.comment,
                            commentaire_interne=actor.thesisdistributionauthorizationactor.internal_comment,
                            motif_refus=actor.thesisdistributionauthorizationactor.rejection_reason,
                        ),
                    )
                    for actor in db_object.thesis_distribution_authorization_group.loaded_actors
                }
                if db_object.thesis_distribution_authorization_group
                else {}
            ),
        )

    @classmethod
    @transaction.atomic
    def save(cls, entity: 'AutorisationDiffusionThese') -> 'AutorisationDiffusionTheseIdentity':
        doctorate = cls._get(entity.entity_id)

        # Update authorization distribution thesis data
        language_id = None
        if entity.langue_redaction_these:
            language_id = Language.objects.values_list('pk', flat=True).get(code=entity.langue_redaction_these)

        doctorate.thesis_distribution_authorization_status = entity.statut.name
        doctorate.funding_sources = entity.sources_financement
        doctorate.thesis_summary_in_english = entity.resume_anglais
        doctorate.thesis_summary_in_other_language = entity.resume_autre_langue
        doctorate.thesis_language_id = language_id
        doctorate.thesis_keywords = entity.mots_cles
        doctorate.thesis_distribution_conditions = (
            entity.type_modalites_diffusion.name if entity.type_modalites_diffusion else ''
        )
        doctorate.thesis_distribution_embargo_date = entity.date_embargo
        doctorate.thesis_distribution_additional_limitation_for_specific_chapters = (
            entity.limitations_additionnelles_chapitres
        )
        doctorate.thesis_distribution_accepted_on = entity.modalites_diffusion_acceptees_le
        doctorate.thesis_distribution_acceptation_content = entity.modalites_diffusion_acceptees

        # Update the signatures
        db_actors: dict[uuid.UUID, Actor] = {}
        persons_by_global_id: dict[str, Person] = {}

        if doctorate.thesis_distribution_authorization_group:
            for db_actor in doctorate.thesis_distribution_authorization_group.loaded_actors:
                db_actors[db_actor.uuid] = db_actor
                persons_by_global_id[db_actor.person.global_id] = db_actor.person
        else:
            # Initialize group if needed
            doctorate.thesis_distribution_authorization_group = Process.objects.create()

        doctorate.save()

        # Retrieve the persons related to new actors
        persons_to_fetch = [
            actor.matricule for actor in entity.signataires.values() if actor.matricule not in persons_by_global_id
        ]

        if persons_to_fetch:
            for person in Person.objects.filter(global_id__in=persons_to_fetch):
                persons_by_global_id[person.global_id] = person

        state_histories: list[StateHistory] = []

        for actor in entity.signataires.values():
            db_actor: ThesisDistributionAuthorizationActor = (
                db_actors.pop(actor.uuid).thesisdistributionauthorizationactor
                if actor.uuid in db_actors
                else ThesisDistributionAuthorizationActor(
                    uuid=actor.uuid,
                    process=doctorate.thesis_distribution_authorization_group,
                )
            )

            # Only update the decision fields if it's a decision state
            if actor.signature.etat.name in {ChoixEtatSignature.APPROVED.name, ChoixEtatSignature.DECLINED.name}:
                db_actor.comment = actor.signature.commentaire_externe
                db_actor.internal_comment = actor.signature.commentaire_interne
                db_actor.rejection_reason = actor.signature.motif_refus

            # Update new fields
            db_actor.role = actor.role.name
            db_actor.person = persons_by_global_id[actor.matricule]

            # Create a new state if it has been updated
            if getattr(db_actor, 'last_state', None) != actor.signature.etat.name:
                state_histories.append(StateHistory(state=actor.signature.etat.name, actor=db_actor))

            db_actor.save()

        # Remove old members
        if db_actors:
            Actor.objects.filter(
                process=doctorate.thesis_distribution_authorization_group,
                uuid__in=db_actors.keys(),
            ).delete()

        # Historize new states
        if state_histories:
            StateHistory.objects.bulk_create(state_histories)

        return entity.entity_id
