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
from typing import Dict, List, Optional

from django.conf import settings
from django.db.models import F, Q, QuerySet
from django.utils.translation import get_language

from base.models.education_group_year import EducationGroupYear
from base.models.entity_version import EntityVersion
from base.models.enums.entity_type import EntityType
from base.models.person import Person
from ddd.logic.reference.domain.model.bourse import BourseIdentity
from infrastructure.reference.domain.service.bourse import BourseTranslator
from osis_common.ddd.interface import ApplicationService, EntityIdentity, RootEntity
from parcours_doctoral.ddd.domain.model._cotutelle import Cotutelle
from parcours_doctoral.ddd.domain.model._experience_precedente_recherche import (
    ExperiencePrecedenteRecherche,
)
from parcours_doctoral.ddd.domain.model._financement import Financement
from parcours_doctoral.ddd.domain.model._formation import FormationIdentity
from parcours_doctoral.ddd.domain.model._institut import InstitutIdentity
from parcours_doctoral.ddd.domain.model._projet import Projet
from parcours_doctoral.ddd.domain.model.enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixDoctoratDejaRealise,
    ChoixSousDomaineSciences,
    ChoixStatutParcoursDoctoral,
    ChoixTypeFinancement,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoral,
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.domain.validator.exceptions import (
    ParcoursDoctoralNonTrouveException,
)
from parcours_doctoral.ddd.dtos import (
    CampusDTO,
    ParcoursDoctoralDTO,
    ParcoursDoctoralRechercheEtudiantDTO,
)
from parcours_doctoral.ddd.dtos.formation import EntiteGestionDTO, FormationDTO
from parcours_doctoral.ddd.dtos.parcours_doctoral import (
    CotutelleDTO,
    FinancementDTO,
    ProjetDTO,
)
from parcours_doctoral.ddd.repository.i_parcours_doctoral import (
    IParcoursDoctoralRepository,
    formater_reference,
)
from parcours_doctoral.models.parcours_doctoral import (
    ParcoursDoctoral as ParcoursDoctoralModel,
)
from program_management.models.education_group_version import EducationGroupVersion
from reference.models.language import Language


class ParcoursDoctoralRepository(IParcoursDoctoralRepository):
    @classmethod
    def delete(cls, entity_id: EntityIdentity, **kwargs: ApplicationService) -> None:
        raise NotImplementedError

    @classmethod
    def search(cls, entity_ids: Optional[List[EntityIdentity]] = None, **kwargs) -> List[RootEntity]:
        raise NotImplementedError

    @classmethod
    def get(cls, entity_id: 'ParcoursDoctoralIdentity') -> 'ParcoursDoctoral':
        try:
            parcours_doctoral: ParcoursDoctoralModel = ParcoursDoctoralModel.objects.select_related(
                'student',
                'training__academic_year',
                'thesis_language',
                'thesis_institute',
            ).get(uuid=entity_id.uuid)
        except ParcoursDoctoralModel.DoesNotExist:
            raise ParcoursDoctoralNonTrouveException

        commission_proximite = None
        if hasattr(ChoixCommissionProximiteCDEouCLSM, parcours_doctoral.proximity_commission):
            commission_proximite = ChoixCommissionProximiteCDEouCLSM[parcours_doctoral.proximity_commission]
        elif hasattr(ChoixCommissionProximiteCDSS, parcours_doctoral.proximity_commission):
            commission_proximite = ChoixCommissionProximiteCDSS[parcours_doctoral.proximity_commission]
        elif hasattr(ChoixSousDomaineSciences, parcours_doctoral.proximity_commission):
            commission_proximite = ChoixSousDomaineSciences[parcours_doctoral.proximity_commission]

        return ParcoursDoctoral(
            entity_id=entity_id,
            statut=ChoixStatutParcoursDoctoral[parcours_doctoral.status],
            reference=parcours_doctoral.reference,
            formation_id=FormationIdentity(
                parcours_doctoral.training.acronym,
                parcours_doctoral.training.academic_year.year,
            ),
            commission_proximite=commission_proximite,
            justification=parcours_doctoral.justification,
            titre_these_propose=parcours_doctoral.thesis_proposed_title,
            experience_precedente_recherche=ExperiencePrecedenteRecherche(
                doctorat_deja_realise=ChoixDoctoratDejaRealise[parcours_doctoral.phd_already_done],
                institution=parcours_doctoral.phd_already_done_institution,
                domaine_these=parcours_doctoral.phd_already_done_thesis_domain,
                date_soutenance=parcours_doctoral.phd_already_done_defense_date,
                raison_non_soutenue=parcours_doctoral.phd_already_done_no_defense_reason,
            ),
            matricule_doctorant=parcours_doctoral.student.global_id,
            cotutelle=Cotutelle(
                motivation=parcours_doctoral.cotutelle_motivation,
                institution_fwb=parcours_doctoral.cotutelle_institution_fwb,
                institution=(
                    str(parcours_doctoral.cotutelle_institution) if parcours_doctoral.cotutelle_institution else ""
                ),
                autre_institution_nom=parcours_doctoral.cotutelle_other_institution_name,
                autre_institution_adresse=parcours_doctoral.cotutelle_other_institution_address,
                demande_ouverture=parcours_doctoral.cotutelle_opening_request,
                convention=parcours_doctoral.cotutelle_convention,
                autres_documents=parcours_doctoral.cotutelle_other_documents,
            ),
            projet=Projet(
                titre=parcours_doctoral.project_title,
                resume=parcours_doctoral.project_abstract,
                documents=parcours_doctoral.project_document,
                langue_redaction_these=(
                    parcours_doctoral.thesis_language.code if parcours_doctoral.thesis_language else ''
                ),
                institut_these=(
                    InstitutIdentity(parcours_doctoral.thesis_institute.uuid)
                    if parcours_doctoral.thesis_institute_id
                    else None
                ),
                lieu_these=parcours_doctoral.thesis_location,
                deja_commence=parcours_doctoral.phd_alread_started,
                deja_commence_institution=parcours_doctoral.phd_alread_started_institute,
                date_debut=parcours_doctoral.work_start_date,
                graphe_gantt=parcours_doctoral.gantt_graph,
                proposition_programme_doctoral=parcours_doctoral.program_proposition,
                projet_formation_complementaire=parcours_doctoral.additional_training_project,
                lettres_recommandation=parcours_doctoral.recommendation_letters,
            ),
            # Financing
            financement=Financement(
                type=(
                    ChoixTypeFinancement[parcours_doctoral.financing_type] if parcours_doctoral.financing_type else None
                ),
                type_contrat_travail=parcours_doctoral.financing_work_contract,
                eft=parcours_doctoral.financing_eft,
                bourse_recherche=(
                    BourseIdentity(uuid=str(parcours_doctoral.international_scholarship_id))
                    if parcours_doctoral.international_scholarship_id
                    else None
                ),
                autre_bourse_recherche=parcours_doctoral.other_international_scholarship,
                bourse_date_debut=parcours_doctoral.scholarship_start_date,
                bourse_date_fin=parcours_doctoral.scholarship_end_date,
                bourse_preuve=parcours_doctoral.scholarship_proof,
                duree_prevue=parcours_doctoral.planned_duration,
                temps_consacre=parcours_doctoral.dedicated_time,
                est_lie_fnrs_fria_fresh_csc=parcours_doctoral.is_fnrs_fria_fresh_csc_linked,
                commentaire=parcours_doctoral.financing_comment,
            ),
        )

    @classmethod
    def verifier_existence(cls, entity_id: 'ParcoursDoctoralIdentity') -> None:  # pragma: no cover
        parcours_doctoral: ParcoursDoctoral = ParcoursDoctoralModel.objects.filter(uuid=entity_id.uuid)
        if not parcours_doctoral:
            raise ParcoursDoctoralNonTrouveException

    @classmethod
    def save(cls, entity: 'ParcoursDoctoral') -> None:
        training = EducationGroupYear.objects.get(
            acronym=entity.formation_id.sigle,
            academic_year__year=entity.formation_id.annee,
        )

        student = Person.objects.get(global_id=entity.matricule_doctorant)

        ParcoursDoctoralModel.objects.update_or_create(
            uuid=entity.entity_id.uuid,
            defaults={
                'status': entity.statut.name,
                'student': student,
                'training': training,
                # Project
                'project_title': entity.projet.titre,
                'project_abstract': entity.projet.resume,
                'thesis_language': (
                    Language.objects.get(code=entity.projet.langue_redaction_these)
                    if entity.projet.langue_redaction_these
                    else None
                ),
                'thesis_institute': (
                    EntityVersion.objects.get(uuid=entity.projet.institut_these.uuid)
                    if entity.projet.institut_these
                    else None
                ),
                'thesis_location': entity.projet.lieu_these,
                'phd_alread_started': entity.projet.deja_commence,
                'phd_alread_started_institute': entity.projet.deja_commence_institution,
                'work_start_date': entity.projet.date_debut,
                'project_document': entity.projet.documents,
                'gantt_graph': entity.projet.graphe_gantt,
                'program_proposition': entity.projet.proposition_programme_doctoral,
                'additional_training_project': entity.projet.projet_formation_complementaire,
                'recommendation_letters': entity.projet.lettres_recommandation,
                'phd_already_done': entity.experience_precedente_recherche.doctorat_deja_realise.name,
                'phd_already_done_institution': entity.experience_precedente_recherche.institution,
                'phd_already_done_thesis_domain': entity.experience_precedente_recherche.domaine_these,
                'phd_already_done_defense_date': entity.experience_precedente_recherche.date_soutenance,
                'phd_already_done_no_defense_reason': entity.experience_precedente_recherche.raison_non_soutenue,
                # Cotutelle
                'cotutelle': bool(entity.cotutelle.motivation),
                'cotutelle_motivation': entity.cotutelle.motivation,
                'cotutelle_institution_fwb': entity.cotutelle.institution_fwb,
                'cotutelle_institution': None if not entity.cotutelle.institution else entity.cotutelle.institution,
                'cotutelle_other_institution_name': entity.cotutelle.autre_institution_nom,
                'cotutelle_other_institution_address': entity.cotutelle.autre_institution_adresse,
                'cotutelle_opening_request': entity.cotutelle.demande_ouverture,
                'cotutelle_convention': entity.cotutelle.convention,
                'cotutelle_other_documents': entity.cotutelle.autres_documents,
                # Financing
                'financing_type': entity.financement.type and entity.financement.type.name or '',
                'financing_work_contract': entity.financement.type_contrat_travail,
                'financing_eft': entity.financement.eft,
                'international_scholarship_id': entity.financement.bourse_recherche
                and entity.financement.bourse_recherche.uuid,
                'other_international_scholarship': entity.financement.autre_bourse_recherche,
                'scholarship_start_date': entity.financement.bourse_date_debut,
                'scholarship_end_date': entity.financement.bourse_date_fin,
                'scholarship_proof': entity.financement.bourse_preuve,
                'planned_duration': entity.financement.duree_prevue,
                'dedicated_time': entity.financement.temps_consacre,
                'is_fnrs_fria_fresh_csc_linked': entity.financement.est_lie_fnrs_fria_fresh_csc,
                'financing_comment': entity.financement.commentaire,
                'proximity_commission': entity.commission_proximite.name if entity.commission_proximite else '',
                'justification': entity.justification,
                # Thesis
                'thesis_proposed_title': entity.titre_these_propose,
            },
        )

    @classmethod
    def get_dto(
        cls,
        entity_id: 'ParcoursDoctoralIdentity' = None,
        proposition_id: 'PropositionIdentity' = None,
    ) -> 'ParcoursDoctoralDTO':
        search_filter = (
            Q(uuid=entity_id.uuid) if entity_id else Q(admission__uuid=proposition_id.uuid) if proposition_id else None
        )

        if not search_filter:
            raise ParcoursDoctoralNonTrouveException

        try:
            parcours_doctoral: ParcoursDoctoralModel = (
                ParcoursDoctoralModel.objects.select_related(
                    'student__birth_country',
                    'international_scholarship',
                    'training__academic_year',
                    'training__education_group_type',
                    'thesis_language',
                    'thesis_institute',
                )
                .annotate_training_management_entity()
                .annotate_with_reference()
                .annotate_with_student_registration_id()
                .annotate_last_status_update()
                .annotate(
                    admission_uuid=F('admission__uuid'),
                    admission_type=F('admission__type'),
                    admission_date=F('admission__approved_by_cdd_at'),
                )
                .annotate_intitule_secteur_formation()
                .get(search_filter)
            )
        except ParcoursDoctoralModel.DoesNotExist:
            raise ParcoursDoctoralNonTrouveException

        i18n_fields_names = cls._get_i18n_fields_names()

        campuses = cls.get_teaching_campuses_dtos([parcours_doctoral.training_id])

        management_entities = cls.get_management_entities_dtos([parcours_doctoral.training.management_entity_id])
        management_entity = management_entities.get(parcours_doctoral.training.management_entity_id)

        return ParcoursDoctoralDTO(
            uuid=str(parcours_doctoral.uuid),
            uuid_admission=str(parcours_doctoral.admission_uuid),  # from annotation
            type_admission=parcours_doctoral.admission_type,  # from annotation
            date_admission_par_cdd=parcours_doctoral.admission_date,  # from annotation
            statut=parcours_doctoral.status,
            date_changement_statut=parcours_doctoral.status_updated_at,  # from annotation
            cree_le=parcours_doctoral.created_at,
            reference=parcours_doctoral.formatted_reference,
            noma_doctorant=parcours_doctoral.student_registration_id or '',  # from annotation
            photo_identite_doctorant=parcours_doctoral.student.id_photo,
            matricule_doctorant=parcours_doctoral.student.global_id,
            nom_doctorant=parcours_doctoral.student.last_name,
            prenom_doctorant=parcours_doctoral.student.first_name,
            genre_doctorant=parcours_doctoral.student.gender,
            date_naissance_doctorant=parcours_doctoral.student.birth_date,
            lieu_naissance_doctorant=parcours_doctoral.student.birth_place,
            pays_naissance_doctorant=(
                parcours_doctoral.student.birth_country.iso_code if parcours_doctoral.student.birth_country else ''
            ),
            commission_proximite=parcours_doctoral.proximity_commission,
            intitule_secteur_formation=parcours_doctoral.intitule_secteur_formation,  # from annotation
            justification=parcours_doctoral.justification,
            formation=FormationDTO(
                sigle=parcours_doctoral.training.acronym,
                code=parcours_doctoral.training.partial_acronym,
                annee=parcours_doctoral.training.academic_year.year,
                intitule=getattr(parcours_doctoral.training, i18n_fields_names['training_title']),
                intitule_fr=parcours_doctoral.training.title,
                intitule_en=parcours_doctoral.training.title_english,
                entite_gestion=management_entity,
                campus=campuses.get(parcours_doctoral.training_id),
                type=parcours_doctoral.training.education_group_type.name,
            ),
            cotutelle=CotutelleDTO(
                cotutelle=parcours_doctoral.cotutelle,
                motivation=parcours_doctoral.cotutelle_motivation,
                institution_fwb=parcours_doctoral.cotutelle_institution_fwb,
                institution=(
                    str(parcours_doctoral.cotutelle_institution) if parcours_doctoral.cotutelle_institution else ""
                ),
                autre_institution=bool(
                    parcours_doctoral.cotutelle_other_institution_name
                    or parcours_doctoral.cotutelle_other_institution_address
                ),
                autre_institution_nom=parcours_doctoral.cotutelle_other_institution_name,
                autre_institution_adresse=parcours_doctoral.cotutelle_other_institution_address,
                demande_ouverture=parcours_doctoral.cotutelle_opening_request,
                convention=parcours_doctoral.cotutelle_convention,
                autres_documents=parcours_doctoral.cotutelle_other_documents,
            ),
            projet=ProjetDTO(
                titre=parcours_doctoral.project_title,
                resume=parcours_doctoral.project_abstract,
                documents_projet=parcours_doctoral.project_document,
                graphe_gantt=parcours_doctoral.gantt_graph,
                proposition_programme_doctoral=parcours_doctoral.program_proposition,
                projet_formation_complementaire=parcours_doctoral.additional_training_project,
                lettres_recommandation=parcours_doctoral.recommendation_letters,
                langue_redaction_these=(
                    parcours_doctoral.thesis_language.code if parcours_doctoral.thesis_language else ''
                ),
                nom_langue_redaction_these=(
                    getattr(
                        parcours_doctoral.thesis_language,
                        i18n_fields_names['language_name'],
                    )
                    if parcours_doctoral.thesis_language
                    else ''
                ),
                institut_these=parcours_doctoral.thesis_institute and parcours_doctoral.thesis_institute.uuid,
                nom_institut_these=parcours_doctoral.thesis_institute
                and parcours_doctoral.thesis_institute.title
                or '',
                sigle_institut_these=parcours_doctoral.thesis_institute
                and parcours_doctoral.thesis_institute.acronym
                or '',
                lieu_these=parcours_doctoral.thesis_location,
                projet_doctoral_deja_commence=parcours_doctoral.phd_alread_started,
                projet_doctoral_institution=parcours_doctoral.phd_alread_started_institute,
                projet_doctoral_date_debut=parcours_doctoral.work_start_date,
                doctorat_deja_realise=parcours_doctoral.phd_already_done,
                institution=parcours_doctoral.phd_already_done_institution,
                domaine_these=parcours_doctoral.phd_already_done_thesis_domain,
                date_soutenance=parcours_doctoral.phd_already_done_defense_date,
                raison_non_soutenue=parcours_doctoral.phd_already_done_no_defense_reason,
            ),
            financement=FinancementDTO(
                type=parcours_doctoral.financing_type,
                type_contrat_travail=parcours_doctoral.financing_work_contract,
                eft=parcours_doctoral.financing_eft,
                bourse_recherche=(
                    BourseTranslator.build_dto(parcours_doctoral.international_scholarship)
                    if parcours_doctoral.international_scholarship
                    else None
                ),
                autre_bourse_recherche=parcours_doctoral.other_international_scholarship,
                bourse_date_debut=parcours_doctoral.scholarship_start_date,
                bourse_date_fin=parcours_doctoral.scholarship_end_date,
                bourse_preuve=parcours_doctoral.scholarship_proof,
                duree_prevue=parcours_doctoral.planned_duration,
                temps_consacre=parcours_doctoral.dedicated_time,
                est_lie_fnrs_fria_fresh_csc=parcours_doctoral.is_fnrs_fria_fresh_csc_linked,
                commentaire=parcours_doctoral.financing_comment,
            ),
        )

    @classmethod
    def get_cotutelle_dto(cls, entity_id: 'ParcoursDoctoralIdentity') -> 'CotutelleDTO':
        return cls.get_dto(entity_id=entity_id).cotutelle

    @classmethod
    def get_teaching_campuses_dtos(cls, training_ids: List[int]) -> Dict[int, CampusDTO]:
        if not training_ids:
            return {}

        education_group_versions = EducationGroupVersion.standard.filter(
            offer_id__in=training_ids,
            transition_name='',
        ).select_related(
            'root_group__main_teaching_campus__country',
        )

        return {
            education_group_version.offer_id: CampusDTO.from_model_object(
                education_group_version.root_group.main_teaching_campus
            )
            for education_group_version in education_group_versions
        }

    @classmethod
    def get_management_entities_dtos(cls, management_entities_ids: List[int]) -> Dict[int, EntiteGestionDTO]:
        if not management_entities_ids:
            return {}

        i18n_fields = {
            settings.LANGUAGE_CODE_EN: {
                'country_name': 'entity__country__name_en',
            },
            settings.LANGUAGE_CODE_FR: {
                'country_name': 'entity__country__name',
            },
        }[get_language()]

        cte = EntityVersion.objects.with_children(
            'acronym',
            'entity_type',
            'title',
            'entity__postal_code',
            'entity__location',
            'entity__city',
            'entity__country__iso_code',
            i18n_fields['country_name'],
            'entity__phone',
            entity_id__in=management_entities_ids,
        )
        qs = cte.queryset().with_cte(cte)

        sector_by_management_entity = {}
        management_entity_by_entity_id = {}

        for entity in qs:
            if entity['entity_type'] == EntityType.SECTOR.name:
                sector_by_management_entity[entity['children'][-1]] = entity

            management_entity_by_entity_id[entity['entity_id']] = entity

        management_entities = {}

        for management_entity_id in management_entities_ids:
            management_entity = management_entity_by_entity_id.get(management_entity_id)

            sector_entity = sector_by_management_entity.get(management_entity_id)

            management_entities[management_entity_id] = (
                EntiteGestionDTO(
                    intitule=management_entity['title'],
                    sigle=management_entity['acronym'],
                    code_secteur=sector_entity['acronym'] if sector_entity else '',
                    intitule_secteur=sector_entity['title'] if sector_entity else '',
                    lieu=management_entity['entity__location'],
                    code_postal=management_entity['entity__postal_code'],
                    ville=management_entity['entity__city'],
                    pays=management_entity['entity__country__iso_code'],
                    nom_pays=management_entity[i18n_fields['country_name']],
                    numero_telephone=management_entity['entity__phone'],
                )
                if management_entity
                else EntiteGestionDTO()
            )

        return management_entities

    @classmethod
    def _get_i18n_fields_names(cls):
        return {
            settings.LANGUAGE_CODE_FR: {
                'training_title': 'title',
                'language_name': 'name',
            },
            settings.LANGUAGE_CODE_EN: {
                'training_title': 'title_english',
                'language_name': 'name_en',
            },
        }[get_language()]

    @classmethod
    def search_dto(
        cls,
        matricule_doctorant: str = None,
        matricule_membre: str = None,
    ) -> List['ParcoursDoctoralRechercheEtudiantDTO']:
        if not matricule_doctorant and not matricule_membre:
            return []

        doctorates: QuerySet[ParcoursDoctoralModel] = ParcoursDoctoralModel.objects.select_related(
            'student',
            'training__academic_year',
            'training__education_group_type',
            'training__enrollment_campus',
        ).order_by('-created_at')

        if matricule_doctorant:
            doctorates = doctorates.filter(
                student__global_id=matricule_doctorant,
            )

        if matricule_membre:
            doctorates = doctorates.filter(
                supervision_group__actors__person__global_id=matricule_membre,
            )

        training_ids = []
        management_entity_ids = []
        for doctorate in doctorates:
            training_ids.append(doctorate.training_id)
            management_entity_ids.append(doctorate.training.management_entity_id)

        campuses = cls.get_teaching_campuses_dtos(training_ids)
        management_entities = cls.get_management_entities_dtos(management_entity_ids)
        i18n_fields_names = cls._get_i18n_fields_names()

        results = []
        for doctorate in doctorates:
            management_entity = management_entities.get(doctorate.training.management_entity_id)
            formatted_reference = formater_reference(
                reference=doctorate.reference,
                nom_campus_inscription=doctorate.training.enrollment_campus.name,
                annee=doctorate.training.academic_year.year,
                sigle_entite_gestion=management_entity.sigle,
            )
            results.append(
                ParcoursDoctoralRechercheEtudiantDTO(
                    uuid=str(doctorate.uuid),
                    reference=formatted_reference,
                    statut=doctorate.status,
                    formation=FormationDTO(
                        sigle=doctorate.training.acronym,
                        code=doctorate.training.partial_acronym,
                        annee=doctorate.training.academic_year.year,
                        intitule=getattr(doctorate.training, i18n_fields_names['training_title']),
                        intitule_fr=doctorate.training.title,
                        intitule_en=doctorate.training.title_english,
                        entite_gestion=management_entity,
                        campus=campuses.get(doctorate.training_id),
                        type=doctorate.training.education_group_type.name,
                    ),
                    matricule_doctorant=doctorate.student.global_id,
                    genre_doctorant=doctorate.student.gender,
                    prenom_doctorant=doctorate.student.first_name,
                    nom_doctorant=doctorate.student.last_name,
                    cree_le=doctorate.created_at,
                )
            )

        return results
