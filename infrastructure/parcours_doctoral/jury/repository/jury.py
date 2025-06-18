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
from django.db import transaction
from django.db.models import Prefetch, Q
from django.utils.translation import get_language

from base.models.person import Person
from osis_common.ddd.interface import ApplicationService, EntityIdentity, RootEntity
from parcours_doctoral.ddd.jury.domain.model.enums import RoleJury
from parcours_doctoral.ddd.jury.domain.model.jury import Jury, JuryIdentity, MembreJury
from parcours_doctoral.ddd.jury.dtos.jury import JuryDTO, MembreJuryDTO
from parcours_doctoral.ddd.jury.repository.i_jury import IJuryRepository
from parcours_doctoral.ddd.jury.validator.exceptions import (
    JuryNonTrouveException,
    MembreNonTrouveDansJuryException,
)
from parcours_doctoral.models import ActorType, ParcoursDoctoralSupervisionActor
from parcours_doctoral.models.jury import JuryMember
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
                    'jury_members',
                    queryset=JuryMember.objects.select_related(
                        'promoter__country',
                        'promoter__person',
                        'person',
                        'country',
                    ),
                )
            )
        )

    @classmethod
    def _get(cls, entity_id: 'JuryIdentity') -> 'ParcoursDoctoral':
        try:
            parcours_doctoral = cls._get_queryset().get(uuid=entity_id.uuid)
        except ParcoursDoctoral.DoesNotExist:
            raise JuryNonTrouveException
        # Initialize promoters members if needed
        if not parcours_doctoral.jury_members.all():
            JuryMember.objects.bulk_create(
                [
                    JuryMember(
                        role=RoleJury.MEMBRE.name,
                        parcours_doctoral=parcours_doctoral,
                        promoter_id=promoter,
                    )
                    for promoter in parcours_doctoral.supervision_group.actors.filter(
                        parcoursdoctoralsupervisionactor__type=ActorType.PROMOTER.name
                    ).values_list('pk', flat=True)
                ]
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
        thesis_language = (
            Language.objects.filter(code=entity.langue_redaction).first() if entity.langue_redaction else None
        )
        defense_language = (
            Language.objects.filter(code=entity.langue_soutenance).first() if entity.langue_soutenance else None
        )
        ParcoursDoctoral.objects.filter(uuid=str(entity.entity_id.uuid)).update(
            thesis_proposed_title=entity.titre_propose,
            defense_method=entity.formule_defense,
            defense_indicative_date=entity.date_indicative,
            thesis_language=thesis_language,
            defense_language=defense_language,
            comment_about_jury=entity.commentaire,
            accounting_situation=entity.situation_comptable,
            jury_approval=entity.approbation_pdf,
        )

        if entity.membres is not None:
            parcours_doctoral = ParcoursDoctoral.objects.get(uuid=entity.entity_id.uuid)
            for membre in entity.membres:
                if membre.est_promoteur:
                    promoter = ParcoursDoctoralSupervisionActor.objects.get(id=membre.matricule)
                    JuryMember.objects.update_or_create(
                        uuid=membre.uuid,
                        parcours_doctoral=parcours_doctoral,
                        defaults={
                            'role': membre.role,
                            'promoter': promoter,
                            'person': None,
                            'institute': '',
                            'other_institute': membre.autre_institution,
                            'country': None,
                            'last_name': '',
                            'first_name': '',
                            'title': '',
                            'non_doctor_reason': '',
                            'gender': '',
                            'email': '',
                        },
                    )
                elif membre.matricule:
                    person = Person.objects.get(global_id=membre.matricule)
                    JuryMember.objects.update_or_create(
                        uuid=membre.uuid,
                        parcours_doctoral=parcours_doctoral,
                        defaults={
                            'role': membre.role,
                            'promoter': None,
                            'person': person,
                            'institute': '',
                            'other_institute': membre.autre_institution,
                            'country': None,
                            'last_name': '',
                            'first_name': '',
                            'title': '',
                            'non_doctor_reason': '',
                            'gender': '',
                            'email': '',
                        },
                    )
                else:
                    country = Country.objects.filter(Q(iso_code=membre.pays) | Q(name=membre.pays)).first()
                    JuryMember.objects.update_or_create(
                        uuid=membre.uuid,
                        parcours_doctoral=parcours_doctoral,
                        defaults={
                            'role': membre.role,
                            'promoter': None,
                            'person': None,
                            'institute': membre.institution,
                            'other_institute': membre.autre_institution,
                            'country': country,
                            'last_name': membre.nom,
                            'first_name': membre.prenom,
                            'title': membre.titre,
                            'non_doctor_reason': membre.justification_non_docteur,
                            'gender': membre.genre,
                            'email': membre.email,
                        },
                    )
            parcours_doctoral.jury_members.exclude(uuid__in=[membre.uuid for membre in entity.membres]).delete()
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
                    role=membre.role,
                    est_promoteur=membre.est_promoteur,
                    matricule=membre.matricule,
                    institution=membre.institution,
                    autre_institution=membre.autre_institution,
                    pays=membre.pays,
                    nom=membre.nom,
                    prenom=membre.prenom,
                    titre=membre.titre,
                    justification_non_docteur=membre.justification_non_docteur,
                    genre=membre.genre,
                    email=membre.email,
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
                if parcours_doctoral.thesis_language
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
        def _get_membrejury_from_model(membre: JuryMember) -> MembreJury:
            if membre.promoter is not None:
                if membre.promoter.person is not None:
                    return MembreJury(
                        uuid=str(membre.uuid),
                        role=membre.role,
                        est_promoteur=True,
                        matricule=str(membre.promoter.id),
                        institution=INSTITUTION_UCL,
                        autre_institution=membre.other_institute,
                        pays=(
                            str(membre.promoter.person.country_of_citizenship)
                            if membre.promoter.person.country_of_citizenship
                            else ''
                        ),
                        nom=membre.promoter.person.last_name,
                        prenom=membre.promoter.person.first_name,
                        titre='',
                        justification_non_docteur='',
                        genre=membre.promoter.person.gender,
                        email=membre.promoter.person.email,
                    )
                else:
                    return MembreJury(
                        uuid=str(membre.uuid),
                        role=membre.role,
                        est_promoteur=True,
                        matricule=str(membre.promoter.id),
                        institution=membre.promoter.institute,
                        autre_institution=membre.other_institute,
                        pays=str(membre.promoter.country),
                        nom=membre.promoter.last_name,
                        prenom=membre.promoter.first_name,
                        titre='',
                        justification_non_docteur='',
                        genre='',
                        email=membre.promoter.email,
                    )
            elif membre.person is not None:
                return MembreJury(
                    uuid=str(membre.uuid),
                    role=membre.role,
                    est_promoteur=False,
                    matricule=membre.person.global_id,
                    institution=INSTITUTION_UCL,
                    autre_institution=membre.other_institute,
                    pays=str(membre.person.country_of_citizenship) if membre.person.country_of_citizenship else '',
                    nom=membre.person.last_name,
                    prenom=membre.person.first_name,
                    titre='',
                    justification_non_docteur='',
                    genre=membre.person.gender,
                    email=membre.person.email,
                )
            else:
                return MembreJury(
                    uuid=str(membre.uuid),
                    role=membre.role,
                    est_promoteur=False,
                    matricule='',
                    institution=membre.institute,
                    autre_institution=membre.other_institute,
                    pays=str(membre.country),
                    nom=membre.last_name,
                    prenom=membre.first_name,
                    titre=membre.title,
                    justification_non_docteur=membre.non_doctor_reason,
                    genre=membre.gender,
                    email=membre.email,
                )

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
            membres=[_get_membrejury_from_model(membre) for membre in parcours_doctoral.jury_members.all()],
        )
