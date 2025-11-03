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
import datetime
from typing import List, Optional, Tuple

from django.db.models import F, OuterRef, Subquery

from assessments.calendar.scores_exam_submission_calendar import (
    ScoresExamSubmissionCalendar,
)
from base.models.student import Student
from deliberation.models.enums.numero_session import Session
from parcours_doctoral.ddd.formation.domain.model.activite import ActiviteIdentity
from parcours_doctoral.ddd.formation.domain.model.evaluation import (
    Evaluation,
    EvaluationIdentity,
)
from parcours_doctoral.ddd.formation.domain.model.inscription_evaluation import (
    InscriptionEvaluationIdentity,
)
from parcours_doctoral.ddd.formation.domain.validator.exceptions import (
    EvaluationNonTrouveeException,
)
from parcours_doctoral.ddd.formation.dtos.evaluation import EvaluationDTO
from parcours_doctoral.ddd.formation.repository.i_evaluation import (
    IEvaluationRepository,
)
from parcours_doctoral.infrastructure.utils import get_doctorate_training_acronym
from parcours_doctoral.models.activity import AssessmentEnrollment


class EvaluationRepository(IEvaluationRepository):
    @classmethod
    def get_periode_encodage_notes(
        cls,
        annee: int,
        session: int,
    ):
        academic_session = ScoresExamSubmissionCalendar().get_academic_session_event(
            target_year=annee,
            session=session,
        )

        return (academic_session.start_date, academic_session.end_date) if academic_session else None

    @classmethod
    def get(cls, entity_id: 'EvaluationIdentity') -> 'Evaluation':
        session_as_text = Session.get_key_session(entity_id.session)
        try:
            assessment = (
                AssessmentEnrollment.objects.annotate(course_uuid=F('course__uuid'))
                .filter_by_learning_year(
                    year=entity_id.annee,
                    acronyms=[entity_id.code_unite_enseignement],
                )
                .get(
                    session=session_as_text,
                    course__parcours_doctoral__student__student__registration_id=entity_id.noma,
                )
            )
            return Evaluation(
                entity_id=entity_id,
                uuid=str(assessment.uuid),
                note_soumise=assessment.submitted_mark,
                note_corrigee=assessment.corrected_mark,
                cours_id=ActiviteIdentity(uuid=str(assessment.course_uuid)),  # From annotation
            )
        except AssessmentEnrollment.DoesNotExist:
            raise EvaluationNonTrouveeException

    @classmethod
    def save(cls, entity: 'Evaluation') -> None:
        AssessmentEnrollment.objects.update_or_create(
            uuid=entity.uuid,
            defaults={
                'submitted_mark': entity.note_soumise,
            },
        )

    @classmethod
    def get_dto_queryset(cls):
        return AssessmentEnrollment.objects.annotate_with_learning_year_info().annotate(
            private_defense_date=F('course__parcours_doctoral__current_private_defense__datetime__date'),
            course_uuid=F('course__uuid'),
            training_acronym=F('course__parcours_doctoral__training__acronym'),
        )

    @classmethod
    def search_dto(
        cls,
        annee: int,
        session: int,
        codes_unite_enseignement: List[str],
    ) -> List[EvaluationDTO]:
        session_as_text = Session.get_key_session(session)

        qs = (
            cls.get_dto_queryset()
            .annotate(
                student_person_id=F('course__parcours_doctoral__student_id'),
            )
            .filter(
                session=session_as_text,
            )
            .filter_by_learning_year(
                acronyms=codes_unite_enseignement,
                year=annee,
            )
        )

        if not qs:
            return []

        encoding_period = cls.get_periode_encodage_notes(
            annee=annee,
            session=session,
        )

        student_registration_ids = {
            student['person_id']: student['registration_id']
            for student in Student.objects.filter(
                person_id__in=[assessment.student_person_id for assessment in qs]
            ).values('registration_id', 'person_id')
        }

        dtos = []

        for assessment in qs:
            dtos.append(
                cls.build_dto_from_db_model(
                    assessment=assessment,
                    noma=student_registration_ids.get(assessment.student_person_id, ''),
                    encoding_period=encoding_period,
                )
            )

        return dtos

    @classmethod
    def get_dto(cls, inscription_id: 'InscriptionEvaluationIdentity') -> EvaluationDTO:
        try:
            assessment = (
                cls.get_dto_queryset()
                .annotate(
                    student_registration_id=Subquery(
                        Student.objects.filter(person_id=OuterRef('course__parcours_doctoral__student_id')).values(
                            'registration_id'
                        )[:1]
                    ),
                )
                .get(uuid=inscription_id.uuid)
            )

        except AssessmentEnrollment.DoesNotExist:
            raise EvaluationNonTrouveeException

        encoding_period = cls.get_periode_encodage_notes(
            annee=assessment.learning_year_academic_year,
            session=Session.get_numero_session(assessment.session),
        )

        return cls.build_dto_from_db_model(
            assessment=assessment,
            noma=assessment.student_registration_id,
            encoding_period=encoding_period,
        )

    @classmethod
    def build_dto_from_db_model(
        cls,
        assessment: AssessmentEnrollment,
        noma: Optional[str],
        encoding_period: Optional[Tuple[datetime.date, datetime.date]],
    ):
        teacher_encoding_deadline = cls.get_echeance_encodage_enseignant(
            date_defense_privee=assessment.private_defense_date,  # From annotation
            periode_encodage=encoding_period,
        )

        return EvaluationDTO(
            annee=assessment.learning_year_academic_year,  # From annotation
            session=Session.get_numero_session(assessment.session),
            noma=noma or '',
            code_unite_enseignement=assessment.learning_year_acronym,  # From annotation
            note_soumise=assessment.submitted_mark,
            note_corrigee=assessment.corrected_mark,
            echeance_enseignant=teacher_encoding_deadline,
            est_desinscrit_tardivement=assessment.late_unenrollment,
            est_inscrit_tardivement=assessment.late_enrollment,
            statut=assessment.status,
            uuid=str(assessment.uuid),
            uuid_activite=str(assessment.course_uuid),  # From annotation
            sigle_formation=get_doctorate_training_acronym(assessment.training_acronym),  # From annotation
            periode_encodage_session=encoding_period,
        )
