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

from django.test import SimpleTestCase, TestCase
from osis_notification.models import WebNotification

from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.student import StudentFactory
from deliberation.models.enums.numero_session import Session
from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.formation.builder.evaluation_builder import (
    EvaluationIdentityBuilder,
)
from parcours_doctoral.ddd.formation.builder.inscription_evaluation_builder import (
    InscriptionEvaluationIdentityBuilder,
)
from parcours_doctoral.ddd.formation.commands import EncoderNoteCommand
from parcours_doctoral.ddd.formation.domain.model.activite import Activite
from parcours_doctoral.ddd.formation.domain.model.enums import (
    CategorieActivite,
    StatutActivite,
    StatutInscriptionEvaluation,
)
from parcours_doctoral.ddd.formation.domain.model.evaluation import Evaluation
from parcours_doctoral.ddd.formation.domain.model.inscription_evaluation import (
    InscriptionEvaluation,
)
from parcours_doctoral.ddd.formation.domain.validator.exceptions import (
    EvaluationNonTrouveeException,
)
from parcours_doctoral.ddd.formation.test.factory.activite import ActiviteFactory
from parcours_doctoral.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from parcours_doctoral.infrastructure.parcours_doctoral.formation.repository.in_memory.activite import (
    ActiviteInMemoryRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.formation.repository.in_memory.evaluation import (
    EvaluationInMemoryRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.formation.repository.in_memory.inscription_evaluation import (
    InscriptionEvaluationInMemoryRepository,
)
from parcours_doctoral.tests.factories.assessment_enrollment import (
    AssessmentEnrollmentFactory,
    AssessmentEnrollmentForClassFactory,
)
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory


class EncoderNoteTestCase(SimpleTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.activite_repository = ActiviteInMemoryRepository
        cls.inscription_evaluation_repository = InscriptionEvaluationInMemoryRepository()
        cls.evaluation_repository = EvaluationInMemoryRepository()
        cls.message_bus = message_bus_in_memory_instance

    def setUp(self):
        super().setUp()

        self.activite = ActiviteFactory(
            categorie=CategorieActivite.UCL_COURSE,
            statut=StatutActivite.SOUMISE,
        )

        self.evaluation = Evaluation(
            entity_id=EvaluationIdentityBuilder.build(
                annee=2020,
                session=3,
                code_unite_enseignement='UE1',
                noma='123',
            ),
            note_soumise='',
            note_corrigee='',
            cours_id=self.activite.entity_id,
            uuid=str(uuid.uuid4()),
        )
        self.inscription = InscriptionEvaluation(
            entity_id=InscriptionEvaluationIdentityBuilder.build_from_uuid(uuid=self.evaluation.uuid),
            cours_id=self.activite.entity_id,
            statut=StatutInscriptionEvaluation.ACCEPTEE,
            session=Session.SEPTEMBER,
            inscription_tardive=True,
            desinscription_tardive=False,
        )

        self.activite_repository.entities = [self.activite]
        self.evaluation_repository.set_entities(entities=[self.evaluation])
        self.inscription_evaluation_repository.set_entities(entities=[self.inscription])

    @classmethod
    def tearDownClass(cls):
        cls.activite_repository.reset()

    def test_encoder_note_superieure_ou_egale_a_10(self):
        cmd = EncoderNoteCommand(
            annee=2020,
            session=3,
            noma='123',
            code_unite_enseignement='UE1',
            note='10',
        )

        identite_evaluation_modifiee = self.message_bus.invoke(cmd)

        evaluation_modifiee: Evaluation = self.evaluation_repository.get(identite_evaluation_modifiee)
        activite_modifiee: Activite = self.activite_repository.get(self.activite.entity_id)

        self.assertEqual(evaluation_modifiee.note_soumise, '10')
        self.assertTrue(activite_modifiee.cours_complete)

    def test_encoder_note_inferieure_a_10(self):
        cmd = EncoderNoteCommand(
            annee=2020,
            session=3,
            noma='123',
            code_unite_enseignement='UE1',
            note='9',
        )

        identite_evaluation_modifiee = self.message_bus.invoke(cmd)

        evaluation_modifiee: Evaluation = self.evaluation_repository.get(identite_evaluation_modifiee)
        activite_modifiee: Activite = self.activite_repository.get(self.activite.entity_id)

        self.assertEqual(evaluation_modifiee.note_soumise, '9')
        self.assertFalse(activite_modifiee.cours_complete)

    def test_encoder_note_non_decimale(self):
        cmd = EncoderNoteCommand(
            annee=2020,
            session=3,
            noma='123',
            code_unite_enseignement='UE1',
            note='S',
        )

        identite_evaluation_modifiee = self.message_bus.invoke(cmd)

        evaluation_modifiee: Evaluation = self.evaluation_repository.get(identite_evaluation_modifiee)
        activite_modifiee: Activite = self.activite_repository.get(self.activite.entity_id)

        self.assertEqual(evaluation_modifiee.note_soumise, 'S')
        self.assertFalse(activite_modifiee.cours_complete)


class EncoderNoteImplementationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.parcours_doctoral = ParcoursDoctoralFactory()

        cls.first_program_manager = ProgramManagerFactory(
            education_group=cls.parcours_doctoral.training.education_group
        )
        cls.second_program_manager = ProgramManagerFactory(
            education_group=cls.parcours_doctoral.training.education_group
        )

    def test_with_unknown_evaluation(self):
        with self.assertRaises(EvaluationNonTrouveeException):
            message_bus_instance.invoke(
                EncoderNoteCommand(
                    annee=2020,
                    session=1,
                    noma='123456',
                    code_unite_enseignement='ABC',
                    note='10',
                )
            )

    def test_with_valid_evaluation(self):
        # First assessment
        first_assessment_enrollment = AssessmentEnrollmentFactory(
            session=Session.JANUARY.name,
            course__parcours_doctoral=self.parcours_doctoral,
        )
        first_assessment_enrollment_for_class = AssessmentEnrollmentForClassFactory(
            session=Session.JANUARY.name,
            course__parcours_doctoral=self.parcours_doctoral,
            course__learning_class_year__learning_component_year__learning_unit_year=(
                first_assessment_enrollment.course.learning_unit_year
            ),
            course__learning_class_year__acronym='A',
        )
        course_for_class = first_assessment_enrollment_for_class.course

        course = first_assessment_enrollment.course
        year = course.learning_unit_year.academic_year.year
        acronym = course.learning_unit_year.acronym
        message_bus_instance.invoke(
            EncoderNoteCommand(
                annee=year,
                session=1,
                noma=course.parcours_doctoral.student.student_set.first().registration_id,
                code_unite_enseignement=acronym,
                note='10',
            )
        )

        first_assessment_enrollment.refresh_from_db()
        course.refresh_from_db()

        self.assertEqual(first_assessment_enrollment.submitted_mark, '10')
        self.assertTrue(course.course_completed)

        # Check that notifications have been submitted
        notifications = WebNotification.objects.all()

        self.assertEqual(len(notifications), 2)

        self.assertCountEqual(
            [notifications[0].person, notifications[1].person],
            [self.first_program_manager.person, self.second_program_manager.person],
        )

        self.assertIn(
            f'Une note a été spécifiée pour une évaluation ({acronym} - session n°1 - {year}-{year+1}).',
            notifications[1].payload,
        )

        # Assessment for class
        message_bus_instance.invoke(
            EncoderNoteCommand(
                annee=year,
                session=1,
                noma=course.parcours_doctoral.student.student_set.first().registration_id,
                code_unite_enseignement=f'{acronym}-A',
                note='15',
            )
        )

        first_assessment_enrollment_for_class.refresh_from_db()
        course_for_class.refresh_from_db()

        self.assertEqual(first_assessment_enrollment_for_class.submitted_mark, '15')
        self.assertTrue(course_for_class.course_completed)

        # Second assessment
        second_assessment_enrollment = AssessmentEnrollmentFactory(
            course=course,
            session=Session.JUNE.name,
        )

        message_bus_instance.invoke(
            EncoderNoteCommand(
                annee=course.learning_unit_year.academic_year.year,
                session=2,
                noma=course.parcours_doctoral.student.student_set.first().registration_id,
                code_unite_enseignement=course.learning_unit_year.acronym,
                note='15',
            )
        )
        first_assessment_enrollment.refresh_from_db()
        second_assessment_enrollment.refresh_from_db()
        course.refresh_from_db()

        self.assertEqual(first_assessment_enrollment.submitted_mark, '10')
        self.assertEqual(second_assessment_enrollment.submitted_mark, '15')
        self.assertTrue(course.course_completed)

        # Other noma but for the same student and the same course
        other_student = StudentFactory(
            person=course.parcours_doctoral.student,
        )

        message_bus_instance.invoke(
            EncoderNoteCommand(
                annee=course.learning_unit_year.academic_year.year,
                session=2,
                noma=other_student.registration_id,
                code_unite_enseignement=course.learning_unit_year.acronym,
                note='17',
            )
        )

        first_assessment_enrollment.refresh_from_db()
        second_assessment_enrollment.refresh_from_db()
        course.refresh_from_db()

        self.assertEqual(first_assessment_enrollment.submitted_mark, '10')
        self.assertEqual(second_assessment_enrollment.submitted_mark, '17')
        self.assertTrue(course.course_completed)

    def test_with_an_invalid_mark(self):
        # First assessment
        first_assessment_enrollment = AssessmentEnrollmentFactory(
            session=Session.JANUARY.name,
        )
        course = first_assessment_enrollment.course

        message_bus_instance.invoke(
            EncoderNoteCommand(
                annee=course.learning_unit_year.academic_year.year,
                session=1,
                noma=course.parcours_doctoral.student.student_set.first().registration_id,
                code_unite_enseignement=course.learning_unit_year.acronym,
                note='S',
            )
        )

        first_assessment_enrollment.refresh_from_db()
        course.refresh_from_db()

        self.assertEqual(first_assessment_enrollment.submitted_mark, 'S')
        self.assertFalse(course.course_completed)

        second_assessment_enrollment = AssessmentEnrollmentFactory(
            course=course,
            session=Session.JUNE.name,
        )

        message_bus_instance.invoke(
            EncoderNoteCommand(
                annee=course.learning_unit_year.academic_year.year,
                session=2,
                noma=course.parcours_doctoral.student.student_set.first().registration_id,
                code_unite_enseignement=course.learning_unit_year.acronym,
                note='9.99',
            )
        )

        first_assessment_enrollment.refresh_from_db()
        second_assessment_enrollment.refresh_from_db()
        course.refresh_from_db()

        self.assertEqual(first_assessment_enrollment.submitted_mark, 'S')
        self.assertEqual(second_assessment_enrollment.submitted_mark, '9.99')
        self.assertFalse(course.course_completed)

        third_assessment_enrollment = AssessmentEnrollmentFactory(
            course=course,
            session=Session.SEPTEMBER.name,
        )

        message_bus_instance.invoke(
            EncoderNoteCommand(
                annee=course.learning_unit_year.academic_year.year,
                session=3,
                noma=course.parcours_doctoral.student.student_set.first().registration_id,
                code_unite_enseignement=course.learning_unit_year.acronym,
                note='10',
            )
        )

        first_assessment_enrollment.refresh_from_db()
        second_assessment_enrollment.refresh_from_db()
        third_assessment_enrollment.refresh_from_db()
        course.refresh_from_db()

        self.assertEqual(first_assessment_enrollment.submitted_mark, 'S')
        self.assertEqual(second_assessment_enrollment.submitted_mark, '9.99')
        self.assertEqual(third_assessment_enrollment.submitted_mark, '10')
        self.assertTrue(course.course_completed)
