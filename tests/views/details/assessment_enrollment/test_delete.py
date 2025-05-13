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

import freezegun
from django.shortcuts import resolve_url
from django.test import TestCase

from base.tests.factories.academic_calendar import AcademicCalendarExamSubmissionFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.session_exam_calendar import (
    BasculementDeliberationCalendarSession1Factory,
    SessionExamCalendarFactory,
)
from deliberation.models.enums.numero_session import Session
from parcours_doctoral.ddd.formation.domain.model.enums import (
    StatutActivite,
    StatutInscriptionEvaluation,
)
from parcours_doctoral.tests.factories.activity import UclCourseFactory
from parcours_doctoral.tests.factories.assessment_enrollment import (
    AssessmentEnrollmentFactory,
)
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory


@freezegun.freeze_time('2024-01-01')
class AssessmentEnrollmentDeleteViewTestCase(TestCase):
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
        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission)

        cls.doctorate = ParcoursDoctoralFactory()
        cls.course = UclCourseFactory(
            learning_unit_year__academic_year=cls.academic_years[1],
            parcours_doctoral=cls.doctorate,
            status=StatutActivite.ACCEPTEE.name,
        )
        cls.other_year_course = UclCourseFactory(
            learning_unit_year__academic_year=cls.academic_years[0],
            parcours_doctoral=cls.doctorate,
            status=StatutActivite.ACCEPTEE.name,
        )

        cls.assessment_enrollment = AssessmentEnrollmentFactory(
            course=cls.course,
            session=Session.JANUARY.name,
            late_enrollment=True,
        )
        cls.other_year_assessment_enrollment = AssessmentEnrollmentFactory(course=cls.other_year_course)

        cls.manager = ProgramManagerFactory(education_group=cls.doctorate.training.education_group).person
        cls.other_manager = ProgramManagerFactory().person

        cls.url = resolve_url(
            'parcours_doctoral:assessment-enrollment:delete',
            uuid=cls.doctorate.uuid,
            enrollment_uuid=cls.assessment_enrollment.uuid,
        )
        cls.other_year_url = resolve_url(
            'parcours_doctoral:assessment-enrollment:delete',
            uuid=cls.doctorate.uuid,
            enrollment_uuid=cls.other_year_assessment_enrollment.uuid,
        )
        cls.list_url = resolve_url('parcours_doctoral:assessment-enrollment', uuid=cls.doctorate.uuid)

    def test_delete_with_other_manager_is_forbidden(self):
        self.client.force_login(self.other_manager.user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 403)

    def test_delete_past_assessment_is_forbidden(self):
        self.client.force_login(self.manager.user)
        response = self.client.delete(self.other_year_url)
        self.assertEqual(response.status_code, 403)

    def test_delete(self):
        self.client.force_login(self.manager.user)

        response = self.client.delete(self.url)

        self.assertRedirects(response=response, expected_url=self.list_url)

        self.assessment_enrollment.refresh_from_db()

        self.assertEqual(self.assessment_enrollment.status, StatutInscriptionEvaluation.DESINSCRITE.name)
        self.assertEqual(self.assessment_enrollment.course, self.course)
        self.assertEqual(self.assessment_enrollment.session, Session.JANUARY.name)
        self.assertEqual(self.assessment_enrollment.late_enrollment, True)

        # Check late unenrollment

        # With private defense date before the end of the encoding period
        self.doctorate.defense_indicative_date = datetime.date(2024, 1, 15)
        self.doctorate.save(update_fields=['defense_indicative_date'])

        self.assessment_enrollment.status = StatutInscriptionEvaluation.ACCEPTEE.name
        self.assessment_enrollment.save(update_fields=['status'])

        with freezegun.freeze_time('2024-01-13'):
            response = self.client.delete(self.url)

            self.assessment_enrollment.refresh_from_db()
            self.assertFalse(self.assessment_enrollment.late_unenrollment)

            self.assessment_enrollment.status = StatutInscriptionEvaluation.ACCEPTEE.name
            self.assessment_enrollment.save(update_fields=['status'])

        with freezegun.freeze_time('2024-01-14'):
            response = self.client.delete(self.url)

            self.assessment_enrollment.refresh_from_db()
            self.assertTrue(self.assessment_enrollment.late_unenrollment)

            # With private defense date not in the encoding period
            self.doctorate.defense_indicative_date = datetime.date(2023, 12, 31)
            self.doctorate.save(update_fields=['defense_indicative_date'])

            self.assessment_enrollment.status = StatutInscriptionEvaluation.ACCEPTEE.name
            self.assessment_enrollment.save(update_fields=['status'])

        # With private defense date after the end of the encoding period
        self.doctorate.defense_indicative_date = datetime.date(2024, 2, 15)
        self.doctorate.save()

        with freezegun.freeze_time('2024-01-31'):
            self.client.force_login(self.manager.user)
            response = self.client.delete(self.url)

            self.assessment_enrollment.refresh_from_db()
            self.assertFalse(self.assessment_enrollment.late_unenrollment)

            self.assessment_enrollment.status = StatutInscriptionEvaluation.ACCEPTEE.name
            self.assessment_enrollment.save(update_fields=['status'])

        with freezegun.freeze_time('2024-02-01'):
            response = self.client.delete(self.url)

            self.assessment_enrollment.refresh_from_db()
            self.assertTrue(self.assessment_enrollment.late_unenrollment)

            self.assessment_enrollment.status = StatutInscriptionEvaluation.ACCEPTEE.name
            self.assessment_enrollment.save(update_fields=['status'])

        # Without private defense date
        self.doctorate.defense_indicative_date = None
        self.doctorate.save()

        with freezegun.freeze_time('2024-01-31'):
            self.client.force_login(self.manager.user)
            response = self.client.delete(self.url)

            self.assessment_enrollment.refresh_from_db()
            self.assertFalse(self.assessment_enrollment.late_unenrollment)

            self.assessment_enrollment.status = StatutInscriptionEvaluation.ACCEPTEE.name
            self.assessment_enrollment.save(update_fields=['status'])

        with freezegun.freeze_time('2024-02-01'):
            response = self.client.delete(self.url)

            self.assessment_enrollment.refresh_from_db()
            self.assertTrue(self.assessment_enrollment.late_unenrollment)

            self.assessment_enrollment.status = StatutInscriptionEvaluation.ACCEPTEE.name
            self.assessment_enrollment.save(update_fields=['status'])
