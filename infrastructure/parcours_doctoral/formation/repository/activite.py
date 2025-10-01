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
from typing import List, Mapping, Optional

from django.db.models import F

from base.models.student import Student
from parcours_doctoral.ddd.builder.parcours_doctoral_identity import (
    ParcoursDoctoralIdentityBuilder,
)
from parcours_doctoral.ddd.formation.builder.activite_identity_builder import (
    ActiviteIdentityBuilder,
)
from parcours_doctoral.ddd.formation.domain.model.activite import (
    Activite,
    ActiviteIdentity,
)
from parcours_doctoral.ddd.formation.domain.model.enums import (
    CategorieActivite,
    ChoixStatutPublication,
    ChoixTypeEpreuve,
    ContexteFormation,
    StatutActivite,
)
from parcours_doctoral.ddd.formation.domain.validator.exceptions import (
    ActiviteNonTrouvee,
)
from parcours_doctoral.ddd.formation.dtos import *
from parcours_doctoral.ddd.formation.dtos.inscription_unite_enseignement import (
    InscriptionUniteEnseignementDTO,
)
from parcours_doctoral.ddd.formation.repository.i_activite import IActiviteRepository
from parcours_doctoral.infrastructure.utils import get_doctorate_training_acronym
from parcours_doctoral.models.activity import Activity


class ActiviteRepository(IActiviteRepository):
    @classmethod
    def get_complementaries_training_for_doctoral_training(cls, entity_id: 'ParcoursDoctoralIdentity') -> List['CoursDTO']:  # type: ignore[override]
        activities = Activity.objects.select_related('parcours_doctoral', 'parent').filter(
            parcours_doctoral__uuid=entity_id.uuid, category=CategorieActivite.COURSE.name
        )
        return [cls._get_dto(activity) for activity in activities]

    @classmethod
    def get(cls, entity_id: 'ActiviteIdentity') -> 'Activite':
        activity = Activity.objects.select_related('parcours_doctoral', 'parent').get(uuid=entity_id.uuid)
        return cls._get(activity, entity_id)

    @classmethod
    def get_multiple(cls, entity_ids: List['ActiviteIdentity']) -> Mapping['ActiviteIdentity', 'Activite']:
        ret = {}
        for activity in cls._get_queryset(entity_ids):
            entity_id = ActiviteIdentityBuilder.build_from_uuid(activity.uuid)
            ret[entity_id] = cls._get(activity, entity_id)
        if len(entity_ids) != len(ret):  # pragma: no cover
            raise ActiviteNonTrouvee
        return ret

    @classmethod
    def get_dto(cls, entity_id: 'ActiviteIdentity') -> ActiviteDTO:
        activity = (
            Activity.objects.annotate_with_learning_year_info()
            .select_related('parcours_doctoral', 'parent')
            .get(uuid=entity_id.uuid)
        )
        return cls._get_dto(activity)

    @classmethod
    def get_dtos(cls, entity_ids: List['ActiviteIdentity']) -> Mapping['ActiviteIdentity', ActiviteDTO]:
        ret = {}
        for activity in cls._get_queryset(entity_ids).annotate_with_learning_year_info():
            entity_id = ActiviteIdentityBuilder.build_from_uuid(activity.uuid)
            ret[entity_id] = cls._get_dto(activity)
        if len(entity_ids) != len(ret):  # pragma: no cover
            raise ActiviteNonTrouvee
        return ret

    @classmethod
    def _get_queryset(cls, entity_ids):
        return Activity.objects.select_related('parcours_doctoral', 'parent').filter(
            uuid__in=[entity_id.uuid for entity_id in entity_ids]
        )

    @classmethod
    def _get(cls, activity, entity_id=None):
        return Activite(
            entity_id=entity_id or ActiviteIdentityBuilder.build_from_uuid(activity.uuid),
            parcours_doctoral_id=ParcoursDoctoralIdentityBuilder.build_from_uuid(activity.parcours_doctoral.uuid),
            contexte=ContexteFormation[activity.context],
            ects=activity.ects,
            categorie=CategorieActivite[activity.category],
            statut=StatutActivite[activity.status],
            parent_id=ActiviteIdentityBuilder.build_from_uuid(activity.parent.uuid) if activity.parent_id else None,
            categorie_parente=CategorieActivite[activity.parent.category] if activity.parent_id else None,
            avis_promoteur_reference=activity.reference_promoter_assent,
            commentaire_promoteur_reference=activity.reference_promoter_comment,
            commentaire_gestionnaire=activity.cdd_comment,
            cours_complete=activity.course_completed,
        )

    @classmethod
    def _get_dto(cls, activity: Activity) -> ActiviteDTO:
        categorie = CategorieActivite[activity.category]
        categorie_parente = CategorieActivite[activity.parent.category] if activity.parent_id else None
        if categorie_parente == CategorieActivite.CONFERENCE and categorie == CategorieActivite.COMMUNICATION:
            return ConferenceCommunicationDTO(
                type=activity.type,
                titre=activity.title,
                comite_selection=activity.committee,
                reference_dial=activity.dial_reference,
                preuve_acceptation=activity.acceptation_proof,
                resume=activity.summary,
                attestation_communication=activity.participating_proof,
                commentaire=activity.comment,
            )
        elif categorie_parente == CategorieActivite.CONFERENCE and categorie == CategorieActivite.PUBLICATION:
            return ConferencePublicationDTO(
                type=activity.type,
                intitule=activity.title,
                auteurs=activity.authors,
                role=activity.role,
                nom_revue_maison_edition=activity.journal,
                date=activity.start_date,
                statut_publication=activity.publication_status and ChoixStatutPublication[activity.publication_status],
                preuve_acceptation=activity.acceptation_proof,
                comite_selection=activity.committee,
                mots_cles=activity.keywords,
                resume=activity.summary,
                reference_dial=activity.dial_reference,
                commentaire=activity.comment,
            )
        elif categorie_parente == CategorieActivite.SEMINAR and categorie == CategorieActivite.COMMUNICATION:
            return SeminaireCommunicationDTO(
                date=activity.start_date,
                en_ligne=activity.is_online,
                site_web=activity.website,
                titre_communication=activity.title,
                orateur_oratrice=activity.authors,
                commentaire=activity.comment,
                attestation_participation=activity.participating_proof,
            )
        elif categorie_parente == CategorieActivite.RESIDENCY and categorie == CategorieActivite.COMMUNICATION:
            return SejourCommunicationDTO(
                type_activite=activity.type,
                type_communication=activity.subtype,
                nom=activity.title,
                date=activity.start_date,
                en_ligne=activity.is_online,
                institution_organisatrice=activity.organizing_institution,
                site_web=activity.website,
                titre_communication=activity.subtitle,
                resume=activity.summary,
                attestation_communication=activity.participating_proof,
                commentaire=activity.comment,
            )
        elif categorie == CategorieActivite.CONFERENCE:
            return ConferenceDTO(
                type=activity.type,
                nom_manifestation=activity.title,
                date_debut=activity.start_date,
                date_fin=activity.end_date,
                nombre_jours=activity.participating_days and float(activity.participating_days),
                en_ligne=activity.is_online,
                pays=activity.country.iso_code if activity.country else None,
                ville=activity.city,
                institution_organisatrice=activity.organizing_institution,
                commentaire=activity.comment,
                site_web=activity.website,
                certificat_participation=activity.participating_proof,
            )
        elif categorie == CategorieActivite.COMMUNICATION:
            return CommunicationDTO(
                type_activite=activity.type,
                type_communication=activity.subtype,
                nom=activity.title,
                date=activity.start_date,
                en_ligne=activity.is_online,
                pays=activity.country.iso_code if activity.country else None,
                ville=activity.city,
                institution_organisatrice=activity.organizing_institution,
                site_web=activity.website,
                titre=activity.subtitle,
                comite_selection=activity.committee,
                reference_dial=activity.dial_reference,
                preuve_acceptation=activity.acceptation_proof,
                resume=activity.summary,
                attestation_communication=activity.participating_proof,
                commentaire=activity.comment,
            )
        elif categorie == CategorieActivite.PUBLICATION:
            return PublicationDTO(
                type=activity.type,
                est_publication_nationale=activity.is_publication_national,
                intitule=activity.title,
                date=activity.start_date,
                auteurs=activity.authors,
                role=activity.role,
                nom_revue_maison_edition=activity.journal,
                preuve_acceptation=activity.acceptation_proof,
                statut_publication=activity.publication_status and ChoixStatutPublication[activity.publication_status],
                avec_comite_de_lecture=activity.with_reading_committee,
                mots_cles=activity.keywords,
                resume=activity.summary,
                reference_dial=activity.dial_reference,
                commentaire=activity.comment,
            )
        elif categorie == CategorieActivite.SEMINAR:
            return SeminaireDTO(
                type=activity.type,
                nom=activity.title,
                pays=activity.country.iso_code if activity.country else None,
                ville=activity.city,
                institution_organisatrice=activity.organizing_institution,
                date_debut=activity.start_date,
                date_fin=activity.end_date,
                volume_horaire=activity.hour_volume,
                volume_horaire_type=activity.hour_volume_type,
                attestation_participation=activity.participating_proof,
            )
        elif categorie == CategorieActivite.RESIDENCY:
            return SejourDTO(
                type=activity.type,
                description=activity.subtitle,
                date_debut=activity.start_date,
                date_fin=activity.end_date,
                institution=activity.organizing_institution,
                pays=activity.country.iso_code if activity.country else None,
                ville=activity.city,
                preuve=activity.participating_proof,
                commentaire=activity.comment,
            )
        elif categorie == CategorieActivite.SERVICE:
            return ServiceDTO(
                type=activity.type,
                nom=activity.title,
                date_debut=activity.start_date,
                date_fin=activity.end_date,
                institution=activity.organizing_institution,
                volume_horaire=activity.hour_volume,
                preuve=activity.participating_proof,
                commentaire=activity.comment,
            )
        elif categorie == CategorieActivite.VAE:
            return ValorisationDTO(
                intitule=activity.title,
                description=activity.subtitle,
                preuve=activity.participating_proof,
                cv=activity.summary,
            )
        elif categorie == CategorieActivite.COURSE:
            return CoursDTO(
                type=activity.type,
                nom=activity.title,
                code=activity.subtitle,
                institution=activity.organizing_institution,
                date_debut=activity.start_date,
                date_fin=activity.end_date,
                volume_horaire=activity.hour_volume,
                avec_evaluation=activity.is_online,
                note=activity.mark,
                titulaire=activity.authors,
                certificat=activity.participating_proof,
                commentaire=activity.comment,
                ects=activity.ects,
            )
        elif categorie == CategorieActivite.UCL_COURSE:
            return CoursUclDTO(
                contexte=ContexteFormation[activity.context],
                annee=activity.learning_year_academic_year,
                code_unite_enseignement=activity.learning_year_acronym,
            )
        elif categorie == CategorieActivite.PAPER:  # pragma: no branch
            return EpreuveDTO(
                type=activity.type and ChoixTypeEpreuve[activity.type],
                commentaire=activity.comment,
            )

    @classmethod
    def delete(cls, entity_id: 'ActiviteIdentity', **kwargs) -> None:
        Activity.objects.get(uuid=entity_id.uuid).delete()

    @classmethod
    def save(cls, activite: 'Activite') -> None:
        # The only data that can be updated through repo are process-related fields
        # (else it would override the other dto-related fields)
        Activity.objects.filter(uuid=activite.entity_id.uuid).update(
            status=activite.statut.name,
            reference_promoter_assent=activite.avis_promoteur_reference,
            reference_promoter_comment=activite.commentaire_promoteur_reference,
            cdd_comment=activite.commentaire_gestionnaire,
            # UCL course fields
            course_completed=activite.cours_complete,
        )

    @classmethod
    def search(cls, parent_id: Optional[ActiviteIdentity] = None, **kwargs) -> List[Activite]:
        qs = Activity.objects.select_related('parcours_doctoral').filter(parent__uuid=parent_id.uuid)
        return [cls._get(activity) for activity in qs]

    @classmethod
    def lister_inscriptions_unites_enseignement(
        cls,
        annee: int,
        code_unite_enseignement: str,
    ) -> List[InscriptionUniteEnseignementDTO]:
        activities = (
            Activity.objects.filter(
                category=CategorieActivite.UCL_COURSE.name,
                status=StatutActivite.ACCEPTEE.name,
            )
            .filter_by_learning_year(acronym=code_unite_enseignement, year=annee)
            .annotate(
                student_person_id=F('parcours_doctoral__student_id'),
                training_acronym=F('parcours_doctoral__training__acronym'),
            )
        )

        if not activities:
            return []

        student_registration_ids = {
            student['person_id']: student['registration_id']
            for student in Student.objects.filter(
                person_id__in=[enrollment.student_person_id for enrollment in activities]
            ).values('registration_id', 'person_id')
        }

        return [
            InscriptionUniteEnseignementDTO(
                noma=student_registration_ids.get(activity.student_person_id, ''),
                annee=annee,
                sigle_formation=get_doctorate_training_acronym(activity.training_acronym),  # From annotation
                code_unite_enseignement=code_unite_enseignement,
            )
            for activity in activities
        ]
