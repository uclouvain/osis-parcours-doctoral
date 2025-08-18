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
import datetime

import freezegun.api
from django.test import TestCase

from base.tests import QueriesAssertionsMixin
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.session_exam_calendar import SessionExamCalendarFactory
from deliberation.models.enums.numero_session import Session
from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.formation.commands import ListerEvaluationsQuery
from parcours_doctoral.ddd.formation.domain.model.enums import (
    StatutActivite,
    StatutInscriptionEvaluation,
)
from parcours_doctoral.tests.factories.assessment_enrollment import (
    AssessmentEnrollmentFactory,
)


@freezegun.api.freeze_time('2024-01-01')
class ListerEvaluationsTestCase(QueriesAssertionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = AcademicYearFactory.produce(2023, 1, 1)

        cls.academic_calendars = [
            SessionExamCalendarFactory(
                academic_calendar__data_year=year,
                academic_calendar__start_date=datetime.date(year.year + 1, 1, 1),
                academic_calendar__end_date=datetime.date(year.year + 1, 1, 31),
                number_session=1,
            )
            for year in cls.academic_years
        ]

    def test_list_with_no_assessment(self):
        with self.assertNumQueriesLessThan(2):
            assessments = message_bus_instance.invoke(
                ListerEvaluationsQuery(
                    annee=2020,
                    session=1,
                    code_unite_enseignement='UE1',
                )
            )

        self.assertEqual(len(assessments), 0)

    def test_list_with_assessments(self):
        first_assessment = AssessmentEnrollmentFactory(
            session=Session.JANUARY.name,
            submitted_mark='15',
            corrected_mark='',
            late_enrollment=False,
            late_unenrollment=True,
            course__learning_unit_year__academic_year__year=2023,
            course__learning_unit_year__acronym='UE1',
            course__status=StatutActivite.ACCEPTEE.name,
            status=StatutInscriptionEvaluation.ACCEPTEE.name,
        )
        second_assessment = AssessmentEnrollmentFactory(
            session=Session.JANUARY.name,
            corrected_mark='16',
            submitted_mark='13',
            late_enrollment=True,
            late_unenrollment=False,
            course__learning_unit_year__academic_year__year=2023,
            course__learning_unit_year__acronym='UE1',
            course__status=StatutActivite.ACCEPTEE.name,
            status=StatutInscriptionEvaluation.DESINSCRITE.name,
        )
        other_session_assessment = AssessmentEnrollmentFactory(
            session=Session.SEPTEMBER.name,
            course__learning_unit_year__academic_year__year=2023,
            course__learning_unit_year__acronym='UE1',
            course__status=StatutActivite.SOUMISE.name,
        )
        other_year_assessment = AssessmentEnrollmentFactory(
            session=Session.JANUARY.name,
            course__learning_unit_year__academic_year__year=2022,
            course__learning_unit_year__acronym='UE1',
            course__status=StatutActivite.SOUMISE.name,
        )
        other_learning_unit_acronym_assessment = AssessmentEnrollmentFactory(
            session=Session.JANUARY.name,
            course__learning_unit_year__academic_year__year=2023,
            course__learning_unit_year__acronym='UE2',
            course__status=StatutActivite.SOUMISE.name,
        )

        with self.assertNumQueriesLessThan(4):
            assessments = message_bus_instance.invoke(
                ListerEvaluationsQuery(
                    annee=2023,
                    session=1,
                    code_unite_enseignement='UE1',
                )
            )

        assessments.sort(key=lambda activity: activity.note)

        self.assertEqual(len(assessments), 2)

        self.assertEqual(assessments[0].uuid, str(first_assessment.uuid))
        self.assertEqual(assessments[0].uuid_activite, str(first_assessment.course.uuid))
        self.assertEqual(assessments[0].statut, first_assessment.status)
        self.assertEqual(assessments[0].annee, 2023)
        self.assertEqual(assessments[0].session, 1)
        self.assertEqual(
            assessments[0].noma,
            first_assessment.course.parcours_doctoral.student.student_set.first().registration_id,
        )
        self.assertEqual(assessments[0].code_unite_enseignement, 'UE1')
        self.assertEqual(assessments[0].note_soumise, '15')
        self.assertEqual(assessments[0].note_corrigee, '')
        self.assertEqual(assessments[0].note, '15')
        self.assertEqual(assessments[0].echeance_enseignant, datetime.date(2024, 1, 31))
        self.assertEqual(assessments[0].est_desinscrit_tardivement, True)
        self.assertEqual(assessments[0].est_inscrit_tardivement, False)

        self.assertEqual(assessments[1].uuid, str(second_assessment.uuid))
        self.assertEqual(assessments[1].uuid_activite, str(second_assessment.course.uuid))
        self.assertEqual(assessments[1].statut, second_assessment.status)
        self.assertEqual(assessments[1].annee, 2023)
        self.assertEqual(assessments[1].session, 1)
        self.assertEqual(
            assessments[1].noma,
            second_assessment.course.parcours_doctoral.student.student_set.first().registration_id,
        )
        self.assertEqual(assessments[1].code_unite_enseignement, 'UE1')
        self.assertEqual(assessments[1].note_soumise, '13')
        self.assertEqual(assessments[1].note_corrigee, '16')
        self.assertEqual(assessments[1].note, '16')
        self.assertEqual(assessments[1].echeance_enseignant, datetime.date(2024, 1, 31))
        self.assertEqual(assessments[1].est_desinscrit_tardivement, False)
        self.assertEqual(assessments[1].est_inscrit_tardivement, True)

    def test_encoding_deadline(self):
        cmd = ListerEvaluationsQuery(
            annee=2023,
            session=1,
            code_unite_enseignement='UE1',
        )

        assessment = AssessmentEnrollmentFactory(
            session=Session.JANUARY.name,
            submitted_mark='15',
            corrected_mark='',
            late_enrollment=False,
            late_unenrollment=True,
            course__learning_unit_year__academic_year__year=2023,
            course__learning_unit_year__acronym='UE1',
            course__status=StatutActivite.ACCEPTEE.name,
            status=StatutInscriptionEvaluation.ACCEPTEE.name,
        )

        doctorate = assessment.course.parcours_doctoral

        # With private defense date in the encoding period
        doctorate.defense_indicative_date = datetime.date(2024, 1, 15)
        doctorate.save(update_fields=['defense_indicative_date'])

        assessments = message_bus_instance.invoke(cmd)
        self.assertEqual(len(assessments), 1)
        self.assertEqual(assessments[0].echeance_enseignant, datetime.date(2024, 1, 13))

        # With private defense date not in the encoding period
        doctorate.defense_indicative_date = datetime.date(2023, 12, 31)
        doctorate.save(update_fields=['defense_indicative_date'])

        assessments = message_bus_instance.invoke(cmd)
        self.assertEqual(len(assessments), 1)
        self.assertEqual(assessments[0].echeance_enseignant, datetime.date(2023, 12, 29))

        # Without private defense date
        doctorate.defense_indicative_date = None
        doctorate.save(update_fields=['defense_indicative_date'])

        assessments = message_bus_instance.invoke(cmd)
        self.assertEqual(len(assessments), 1)
        self.assertEqual(assessments[0].echeance_enseignant, datetime.date(2024, 1, 31))
