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

from django.db.models import Case, When

from deliberation.models.enums.numero_session import Session
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.formation.domain.model.activite import ActiviteIdentity
from parcours_doctoral.ddd.formation.domain.model.enums import (
    StatutInscriptionEvaluation,
)
from parcours_doctoral.ddd.formation.domain.model.inscription_evaluation import (
    InscriptionEvaluation,
    InscriptionEvaluationIdentity,
)
from parcours_doctoral.ddd.formation.domain.validator.exceptions import (
    ActiviteNonTrouvee,
    InscriptionEvaluationNonTrouveeException,
)
from parcours_doctoral.ddd.formation.dtos.inscription_evaluation import (
    InscriptionEvaluationDTO,
)
from parcours_doctoral.ddd.formation.repository.i_inscription_evaluation import (
    IInscriptionEvaluationRepository,
)
from parcours_doctoral.models import Activity
from parcours_doctoral.models.activity import AssessmentEnrollment


class InscriptionEvaluationRepository(IInscriptionEvaluationRepository):
    @classmethod
    def _get_domain_object_from_db_object(cls, enrollment: AssessmentEnrollment) -> InscriptionEvaluation:
        return InscriptionEvaluation(
            entity_id=InscriptionEvaluationIdentity(uuid=str(enrollment.uuid)),
            cours_id=ActiviteIdentity(uuid=str(enrollment.course.uuid)),
            session=Session[enrollment.session],
            inscription_tardive=enrollment.late_enrollment,
            statut=StatutInscriptionEvaluation[enrollment.status],
            desinscription_tardive=enrollment.late_unenrollment,
        )

    @classmethod
    def _get_dto_from_db_object(
        cls,
        enrollment: AssessmentEnrollment,
    ) -> InscriptionEvaluationDTO:
        return InscriptionEvaluationDTO(
            uuid=str(enrollment.uuid),
            uuid_activite=str(enrollment.course.uuid),
            session=enrollment.session,
            inscription_tardive=enrollment.late_enrollment,
            desinscription_tardive=enrollment.late_unenrollment,
            code_unite_enseignement=enrollment.course.learning_unit_year.acronym,
            intitule_unite_enseignement=enrollment.course.learning_unit_year.complete_title_i18n,
            annee_unite_enseignement=enrollment.course.learning_unit_year.academic_year.year,
            statut=enrollment.status,
        )

    @classmethod
    def _get_domain_object_qs(cls):
        return AssessmentEnrollment.objects.select_related(
            'course',
        )

    @classmethod
    def _get_dto_qs(cls):
        return AssessmentEnrollment.objects.select_related(
            'course',
            'course__learning_unit_year__academic_year',
            'course__learning_unit_year__learning_container_year',
        )

    @classmethod
    def get(cls, entity_id: 'InscriptionEvaluationIdentity') -> 'InscriptionEvaluation':  # type: ignore[override]
        try:
            enrollment = cls._get_domain_object_qs().get(uuid=entity_id.uuid)
            return cls._get_domain_object_from_db_object(enrollment=enrollment)
        except AssessmentEnrollment.DoesNotExist:
            raise InscriptionEvaluationNonTrouveeException

    @classmethod
    def get_dto(cls, entity_id: 'InscriptionEvaluationIdentity') -> 'InscriptionEvaluationDTO':
        try:
            enrollment = cls._get_dto_qs().get(uuid=entity_id.uuid)
            return cls._get_dto_from_db_object(enrollment=enrollment)
        except AssessmentEnrollment.DoesNotExist:
            raise InscriptionEvaluationNonTrouveeException

    @classmethod
    def delete(cls, entity_id: 'InscriptionEvaluationIdentity', **kwargs) -> None:  # type: ignore[override]
        nb_deletions = AssessmentEnrollment.objects.filter(uuid=entity_id.uuid).delete()

        if not nb_deletions:
            raise InscriptionEvaluationNonTrouveeException

    @classmethod
    def save(cls, entity: 'InscriptionEvaluation') -> None:  # type: ignore[override]
        try:
            related_activity_id = Activity.objects.only('id').get(uuid=entity.cours_id.uuid).id
        except Activity.DoesNotExist:
            raise ActiviteNonTrouvee

        AssessmentEnrollment.objects.update_or_create(
            uuid=entity.entity_id.uuid,
            defaults={
                'course_id': related_activity_id,
                'session': entity.session.name,
                'late_enrollment': entity.inscription_tardive,
                'status': entity.statut.name,
                'late_unenrollment': entity.desinscription_tardive,
            },
        )

    @classmethod
    def search(
        cls,
        cours_id: Optional[ActiviteIdentity] = None,
        parcours_doctoral_id: Optional[ParcoursDoctoralIdentity] = None,
        **kwargs,
    ) -> List[InscriptionEvaluation]:  # type: ignore[override]
        qs = cls._get_domain_object_qs()

        if cours_id is not None:
            qs = qs.filter(course__uuid=cours_id.uuid)

        if parcours_doctoral_id is not None:
            qs = qs.filter(course__parcours_doctoral__uuid=parcours_doctoral_id.uuid)

        return [cls._get_domain_object_from_db_object(enrollment=enrollment) for enrollment in qs]

    @classmethod
    def search_dto(
        cls,
        cours_uuid: Optional[str] = None,
        parcours_doctoral_id: Optional[str] = None,
        **kwargs,
    ) -> List[InscriptionEvaluationDTO]:  # type: ignore[override]
        qs = cls._get_dto_qs()

        if cours_uuid is not None:
            qs = qs.filter(course__uuid=cours_uuid)

        if parcours_doctoral_id is not None:
            qs = qs.filter(course__parcours_doctoral__uuid=parcours_doctoral_id)

        qs = qs.with_session_numero()

        qs = qs.order_by(
            'course__learning_unit_year__academic_year__year',
            'session_numero',
            'course__learning_unit_year__acronym',
        )

        return [cls._get_dto_from_db_object(enrollment=enrollment) for enrollment in qs]
