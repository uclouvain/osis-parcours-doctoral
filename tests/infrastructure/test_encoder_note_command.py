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
from django.test import TestCase
from osis_notification.models import WebNotification

from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.student import StudentFactory
from deliberation.models.enums.numero_session import Session
from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.formation.commands import EncoderNoteCommand
from parcours_doctoral.ddd.formation.domain.validator.exceptions import (
    EvaluationNonTrouveeException,
)
from parcours_doctoral.infrastructure.parcours_doctoral.domain.service.notification import (
    Notification,
)
from parcours_doctoral.tests.factories.assessment_enrollment import (
    AssessmentEnrollmentFactory,
)
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory


class EncoderNoteCommandTestCase(TestCase):
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
