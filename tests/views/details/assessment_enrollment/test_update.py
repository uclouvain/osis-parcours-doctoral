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

import freezegun
from django.shortcuts import resolve_url
from django.test import TestCase

from base.forms.utils import EMPTY_CHOICE
from base.tests.factories.academic_calendar import AcademicCalendarExamSubmissionFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from deliberation.models.enums.numero_session import Session
from parcours_doctoral.ddd.formation.domain.model.enums import StatutActivite
from parcours_doctoral.tests.factories.activity import UclCourseFactory
from parcours_doctoral.tests.factories.assessment_enrollment import (
    AssessmentEnrollmentFactory,
)
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory


@freezegun.freeze_time('2024-01-01')
class AssessmentEnrollmentUpdateViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = AcademicYearFactory.produce(2023, 1, 1)

        cls.academic_calendars = [AcademicCalendarExamSubmissionFactory(data_year=year) for year in cls.academic_years]

        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission)

        cls.doctorate = ParcoursDoctoralFactory()
        cls.course = UclCourseFactory(
            learning_unit_year__academic_year=cls.academic_years[1],
            parcours_doctoral=cls.doctorate,
            status=StatutActivite.ACCEPTEE.name,
        )
        cls.not_accepted_course = UclCourseFactory(
            learning_unit_year__academic_year=cls.academic_years[1],
            parcours_doctoral=cls.doctorate,
            status=StatutActivite.NON_SOUMISE.name,
        )
        cls.other_year_course = UclCourseFactory(
            learning_unit_year__academic_year=cls.academic_years[0],
            parcours_doctoral=cls.doctorate,
            status=StatutActivite.ACCEPTEE.name,
        )

        cls.assessment_enrollment = AssessmentEnrollmentFactory(course=cls.course)
        cls.other_year_assessment_enrollment = AssessmentEnrollmentFactory(course=cls.other_year_course)

        cls.manager = ProgramManagerFactory(education_group=cls.doctorate.training.education_group).person
        cls.other_manager = ProgramManagerFactory().person

        cls.url = resolve_url(
            'parcours_doctoral:assessment-enrollment:update',
            uuid=cls.doctorate.uuid,
            enrollment_uuid=cls.assessment_enrollment.uuid,
        )
        cls.other_year_url = resolve_url(
            'parcours_doctoral:assessment-enrollment:update',
            uuid=cls.doctorate.uuid,
            enrollment_uuid=cls.other_year_assessment_enrollment.uuid,
        )
        cls.list_url = resolve_url('parcours_doctoral:assessment-enrollment', uuid=cls.doctorate.uuid)

    def test_get_with_other_manager_is_forbidden(self):
        self.client.force_login(self.other_manager.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_form_current_year(self):
        self.client.force_login(self.manager.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        # Check context data
        self.assertEqual(response.context['assessment_enrollment'].uuid, str(self.assessment_enrollment.uuid))
        self.assertEqual(response.context['current_year'], self.academic_years[1].year)
        self.assertCountEqual(response.context['score_exam_submission_sessions'], [self.academic_calendars[1]])

        # Check form
        form = response.context['form']

        self.assertTrue(form.fields['course'].disabled)
        self.assertEqual(len(form.fields['course'].choices), 2)
        self.assertEqual(form.fields['course'].choices[0], EMPTY_CHOICE[0])
        self.assertEqual(
            form.fields['course'].choices[1],
            (
                str(self.course.uuid),
                f'{self.course.learning_unit_year.acronym} - {self.course.learning_unit_year.complete_title_i18n}',
            ),
        )
        self.assertFalse(form.fields['session'].disabled)
        self.assertFalse(form.fields['late_enrollment'].disabled)

    def test_get_form_other_year(self):
        self.client.force_login(self.manager.user)

        response = self.client.get(self.other_year_url)

        self.assertEqual(response.status_code, 403)

    def test_post_form(self):
        self.client.force_login(self.manager.user)

        response = self.client.post(
            self.url,
            data={
                'late_enrollment': 'on',
                'session': Session.SEPTEMBER.name,
            },
        )

        self.assertRedirects(response=response, expected_url=self.list_url)

        self.assessment_enrollment.refresh_from_db()

        self.assertEqual(self.assessment_enrollment.course, self.course)
        self.assertEqual(self.assessment_enrollment.session, Session.SEPTEMBER.name)
        self.assertEqual(self.assessment_enrollment.status, StatutActivite.ACCEPTEE.name)
        self.assertEqual(self.assessment_enrollment.late_enrollment, True)
