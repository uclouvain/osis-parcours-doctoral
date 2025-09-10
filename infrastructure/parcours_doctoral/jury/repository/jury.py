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
from typing import List, Optional

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import F, Prefetch, Q
from django.db.models.functions import Coalesce
from django.utils.translation import get_language
from osis_signature.models import Actor, Process, StateHistory

from base.models.person import Person
from osis_common.ddd.interface import ApplicationService, EntityIdentity, RootEntity
from parcours_doctoral.auth.roles.jury_member import JuryMember
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.jury.domain.model.enums import (
    ChoixEtatSignature,
    ChoixStatutSignature,
    GenreMembre,
    RoleJury,
    TitreMembre,
)
from parcours_doctoral.ddd.jury.domain.model.jury import (
    Jury,
    JuryIdentity,
    MembreJury,
    SignatureMembre,
)
from parcours_doctoral.ddd.jury.dtos.jury import (
    JuryDTO,
    MembreJuryDTO,
    SignatureMembreJuryDTO,
)
from parcours_doctoral.ddd.jury.repository.i_jury import IJuryRepository
from parcours_doctoral.ddd.jury.validator.exceptions import (
    JuryNonTrouveException,
    MembreNonTrouveDansJuryException,
)
from parcours_doctoral.models import ActorType, ParcoursDoctoralSupervisionActor
from parcours_doctoral.models.jury import JuryActor
from parcours_doctoral.models.parcours_doctoral import ParcoursDoctoral
from reference.models.country import Country
from reference.models.language import Language

INSTITUTION_UCL = "UCLouvain"


class JuryRepository(IJuryRepository):
    @classmethod
    def delete(cls, entity_id: EntityIdentity, **kwargs: ApplicationService) -> None:
        raise NotImplementedError

    @classmethod
    def search(cls, entity_ids: Optional[List[EntityIdentity]] = None, **kwargs) -> List[RootEntity]:
        raise NotImplementedError

    @classmethod
    def _get_queryset(cls):
        return (
            ParcoursDoctoral.objects.only(
                "uuid",
                "thesis_language",
                "thesis_proposed_title",
                "defense_method",
                "defense_indicative_date",
                "defense_language",
                "comment_about_jury",
                "accounting_situation",
                "jury_approval",
            )
            .select_related(
                "thesis_language",
                "defense_language",
            )
            .prefetch_related(
                Prefetch(
                    'jury_group__actors',
                    Actor.objects.alias(dynamic_last_name=Coalesce(F('last_name'), F('person__last_name')))
                    .select_related('juryactor')
                    .order_by('dynamic_last_name'),
                    to_attr='ordered_members',
                )
            )
        )

    @classmethod
    def _get(cls, entity_id: 'JuryIdentity') -> 'ParcoursDoctoral':
        try:
            parcours_doctoral = cls._get_queryset().get(uuid=entity_id.uuid)
        except ParcoursDoctoral.DoesNotExist:
            raise JuryNonTrouveException
        # Initialize group if needed
        if not parcours_doctoral.jury_group_id:
            with transaction.atomic():
                parcours_doctoral.jury_group = Process.objects.create()
                parcours_doctoral.save(update_fields=['jury_group'])

                for promoter in parcours_doctoral.supervision_group.actors.filter(
                    parcoursdoctoralsupervisionactor__type=ActorType.PROMOTER.name
                ):
                    JuryActor.objects.create(
                        process=parcours_doctoral.jury_group,
                        role=RoleJury.MEMBRE.name,
                        is_promoter=True,
                        is_lead_promoter=promoter.parcoursdoctoralsupervisionactor.is_reference_promoter,
                        **(
                            {'person_id': promoter.person_id}
                            if promoter.person_id
                            else {
                                'first_name': promoter.first_name,
                                'last_name': promoter.last_name,
                                'email': promoter.email,
                                'institute': promoter.institute,
                                'city': promoter.city,
                                'country_id': promoter.country_id,
                                'language': promoter.language,
                            }
                        ),
                    )

            # reload with members
            parcours_doctoral = cls._get_queryset().get(uuid=entity_id.uuid)
        return parcours_doctoral

    @classmethod
    def get_dto(cls, entity_id: 'JuryIdentity') -> 'JuryDTO':
        return cls._load_jury_dto(cls._get(entity_id))

    @classmethod
    def get_membre_dto(cls, entity_id: 'JuryIdentity', membre_uuid: str) -> MembreJuryDTO:
        jury = cls.get_dto(entity_id)
        for membre in jury.membres:
            if str(membre.uuid) == membre_uuid:
                return membre
        raise MembreNonTrouveDansJuryException(jury=jury, uuid_membre=membre_uuid)

    @classmethod
    def get(cls, entity_id: 'JuryIdentity') -> 'Jury':
        return cls._load_jury(cls._get(entity_id))

    @classmethod
    @transaction.atomic
    def save(cls, entity: 'Jury') -> 'JuryIdentity':
        codes = list(filter(None, [entity.langue_redaction, entity.langue_soutenance]))
        languages_by_code = {lang.code: lang for lang in Language.objects.filter(code__in=codes)}

        ParcoursDoctoral.objects.filter(uuid=str(entity.entity_id.uuid)).update(
            thesis_proposed_title=entity.titre_propose,
            defense_method=entity.formule_defense,
            defense_indicative_date=entity.date_indicative,
            thesis_language=languages_by_code.get(entity.langue_redaction, None),
            defense_language=languages_by_code.get(entity.langue_soutenance, None),
            comment_about_jury=entity.commentaire,
            accounting_situation=entity.situation_comptable,
            jury_approval=entity.approbation_pdf,
        )

        current_parcours_doctoral = cls._get_queryset().get(uuid=entity.entity_id.uuid)
        if entity.membres:
            # Remove old members
            current_parcours_doctoral.jury_group.actors.exclude(
                uuid__in=[membre.uuid for membre in entity.membres]
            ).delete()

            for membre in entity.membres:
                # We cannot use update_or_create as JuryActor inherits from another models and we get an error
                try:
                    actor = JuryActor.objects.get(uuid=membre.uuid, process=current_parcours_doctoral.jury_group)
                    is_create = False
                except JuryActor.DoesNotExist:
                    actor = JuryActor(uuid=membre.uuid, process=current_parcours_doctoral.jury_group)
                    is_create = True

                # Handle signature
                if actor.pk is not None and actor.state != membre.signature.etat.name:
                    StateHistory.objects.create(state=membre.signature.etat.name, actor_id=actor.id)
                if membre.signature.etat.name in [ChoixEtatSignature.APPROVED.name, ChoixEtatSignature.DECLINED.name]:
                    actor.comment = membre.signature.commentaire_externe
                    actor.pdf_from_candidate = membre.signature.pdf
                    actor.internal_comment = membre.signature.commentaire_interne
                    actor.rejection_reason = membre.signature.motif_refus

                # Handle the rest
                if membre.matricule:
                    person = Person.objects.get(global_id=membre.matricule)
                    values = {
                        'role': membre.role.name if membre.role else '',
                        'is_promoter': membre.est_promoteur,
                        'is_lead_promoter': membre.est_promoteur_de_reference,
                        'person': person,
                        'institute': '',
                        'first_name': '',
                        'last_name': '',
                        'email': '',
                        'country_id': None,
                        'other_institute': membre.autre_institution,
                        'title': '',
                        'non_doctor_reason': '',
                        'gender': '',
                    }
                    JuryMember.objects.update_or_create(person=person)
                else:
                    country = Country.objects.filter(Q(iso_code=membre.pays) | Q(name=membre.pays)).first()
                    values = {
                        'role': membre.role.name if membre.role else '',
                        'is_promoter': membre.est_promoteur,
                        'is_lead_promoter': membre.est_promoteur_de_reference,
                        'person': None,
                        'institute': membre.institution,
                        'first_name': membre.prenom,
                        'last_name': membre.nom,
                        'email': membre.email,
                        'country': country,
                        'other_institute': membre.autre_institution,
                        'title': membre.titre.name if membre.titre else '',
                        'non_doctor_reason': membre.justification_non_docteur,
                        'gender': membre.genre.name if membre.genre else '',
                        'language': membre.langue,
                        # Required to be not empty by Actor constraints
                        'city': 'x',
                    }

                for key, value in values.items():
                    setattr(actor, key, value)
                actor.save()

                if is_create and membre.signature.etat.name != ChoixEtatSignature.NOT_INVITED.name:
                    StateHistory.objects.create(state=membre.signature.etat.name, actor_id=actor.id)

        return entity.entity_id

    @classmethod
    def _load_jury_dto(cls, parcours_doctoral: ParcoursDoctoral) -> JuryDTO:
        jury = cls._load_jury(parcours_doctoral)
        if get_language() == settings.LANGUAGE_CODE_FR:
            lang_name_attribute = 'name'
        else:
            lang_name_attribute = 'name_en'

        return JuryDTO(
            uuid=jury.entity_id.uuid,
            titre_propose=jury.titre_propose,
            membres=[
                MembreJuryDTO(
                    uuid=membre.uuid,
                    role=membre.role.name if membre.role else '',
                    est_promoteur=membre.est_promoteur,
                    est_promoteur_de_reference=membre.est_promoteur_de_reference,
                    matricule=membre.matricule,
                    institution=membre.institution,
                    autre_institution=membre.autre_institution,
                    pays=membre.pays,
                    nom=membre.nom,
                    prenom=membre.prenom,
                    titre=membre.titre.name if membre.titre else '',
                    justification_non_docteur=membre.justification_non_docteur,
                    genre=membre.genre.name if membre.genre else '',
                    langue=membre.langue,
                    email=membre.email,
                    signature=SignatureMembreJuryDTO(
                        etat=membre.signature.etat.name if membre.signature.etat else '',
                        date=membre.signature.date,
                        commentaire_externe=membre.signature.commentaire_externe,
                        commentaire_interne=membre.signature.commentaire_interne,
                        motif_refus=membre.signature.motif_refus,
                        pdf=membre.signature.pdf,
                    ),
                )
                for membre in jury.membres
            ],
            formule_defense=jury.formule_defense,
            date_indicative=jury.date_indicative,
            nom_langue_redaction=(
                getattr(parcours_doctoral.thesis_language, lang_name_attribute)
                if parcours_doctoral.thesis_language
                else ''
            ),
            langue_redaction=jury.langue_redaction,
            nom_langue_soutenance=(
                getattr(parcours_doctoral.defense_language, lang_name_attribute)
                if parcours_doctoral.defense_language
                else ''
            ),
            langue_soutenance=jury.langue_soutenance,
            commentaire=jury.commentaire,
            situation_comptable=jury.situation_comptable,
            approbation_pdf=jury.approbation_pdf,
        )

    @classmethod
    def _load_jury(
        cls,
        parcours_doctoral: 'ParcoursDoctoral',
    ) -> Jury:
        def _get_membrejury_from_model(actor: JuryActor) -> MembreJury:
            PERSON_GENDER_TO_GENRE_MEMBRE = {
                'F': GenreMembre.FEMININ,
                'H': GenreMembre.MASCULIN,
                'X': GenreMembre.AUTRE,
            }

            if actor.person is not None:
                return MembreJury(
                    uuid=str(actor.uuid),
                    role=RoleJury[actor.juryactor.role] if actor.juryactor.role else None,
                    est_promoteur=actor.juryactor.is_promoter,
                    est_promoteur_de_reference=actor.juryactor.is_lead_promoter,
                    matricule=actor.person.global_id,
                    institution=INSTITUTION_UCL,
                    autre_institution=actor.juryactor.other_institute,
                    pays=str(actor.person.country_of_citizenship) if actor.person.country_of_citizenship else '',
                    nom=actor.person.last_name,
                    prenom=actor.person.first_name,
                    titre=None,
                    justification_non_docteur='',
                    genre=PERSON_GENDER_TO_GENRE_MEMBRE.get(actor.person.gender, ''),
                    langue=actor.person.language,
                    email=actor.person.email,
                    signature=SignatureMembre(
                        etat=ChoixEtatSignature[actor.state],
                        date=actor.last_state_date,
                        commentaire_externe=actor.comment,
                        commentaire_interne=actor.juryactor.internal_comment,
                        motif_refus=actor.juryactor.rejection_reason,
                        pdf=actor.juryactor.pdf_from_candidate,
                    ),
                )
            else:
                return MembreJury(
                    uuid=str(actor.uuid),
                    role=RoleJury[actor.juryactor.role] if actor.juryactor.role else None,
                    est_promoteur=actor.juryactor.is_promoter,
                    est_promoteur_de_reference=actor.juryactor.is_lead_promoter,
                    matricule='',
                    institution=actor.institute,
                    autre_institution=actor.juryactor.other_institute,
                    pays=str(actor.country),
                    nom=actor.last_name,
                    prenom=actor.first_name,
                    titre=TitreMembre[actor.juryactor.title] if actor.juryactor.title else None,
                    justification_non_docteur=actor.juryactor.non_doctor_reason,
                    genre=GenreMembre[actor.juryactor.gender] if actor.juryactor.gender else None,
                    langue=actor.language,
                    email=actor.email,
                    signature=SignatureMembre(
                        etat=ChoixEtatSignature[actor.state],
                        date=actor.last_state_date,
                        commentaire_externe=actor.comment,
                        commentaire_interne=actor.juryactor.internal_comment,
                        motif_refus=actor.juryactor.rejection_reason,
                        pdf=actor.juryactor.pdf_from_candidate,
                    ),
                )

        if parcours_doctoral.status == ChoixStatutParcoursDoctoral.JURY_SOUMIS.name:
            statut_signature = ChoixStatutSignature.SIGNING_IN_PROGRESS
        elif parcours_doctoral.status == ChoixStatutParcoursDoctoral.JURY_SOUMIS.name:
            statut_signature = ChoixStatutSignature.SIGNED
        else:
            statut_signature = ChoixStatutSignature.IN_PROGRESS

        return Jury(
            entity_id=JuryIdentity(uuid=str(parcours_doctoral.uuid)),
            titre_propose=parcours_doctoral.thesis_proposed_title,
            formule_defense=parcours_doctoral.defense_method,
            date_indicative=parcours_doctoral.defense_indicative_date,
            langue_redaction=parcours_doctoral.thesis_language.code if parcours_doctoral.thesis_language else '',
            langue_soutenance=parcours_doctoral.defense_language.code if parcours_doctoral.defense_language else '',
            commentaire=parcours_doctoral.comment_about_jury,
            situation_comptable=parcours_doctoral.accounting_situation,
            approbation_pdf=parcours_doctoral.jury_approval,
            statut_signature=statut_signature,
            membres=[_get_membrejury_from_model(membre) for membre in parcours_doctoral.jury_group.ordered_members],
        )
