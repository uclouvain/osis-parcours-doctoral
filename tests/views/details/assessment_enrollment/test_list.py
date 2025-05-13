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

from typing import Dict, List

from django.shortcuts import resolve_url
from django.test import TestCase

from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from deliberation.models.enums.numero_session import Session
from parcours_doctoral.ddd.formation.domain.model.enums import (
    StatutInscriptionEvaluation,
)
from parcours_doctoral.ddd.formation.dtos.inscription_evaluation import (
    InscriptionEvaluationDTO,
)
from parcours_doctoral.models import AssessmentEnrollment
from parcours_doctoral.tests.factories.assessment_enrollment import (
    AssessmentEnrollmentFactory,
)
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory


class AssessmentEnrollmentListViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission)

        cls.doctorate = ParcoursDoctoralFactory()

        cls.manager = ProgramManagerFactory(education_group=cls.doctorate.training.education_group).person
        cls.other_manager = ProgramManagerFactory().person

        cls.url = resolve_url('parcours_doctoral:assessment-enrollment', uuid=cls.doctorate.uuid)

    def test_get_with_other_manager_is_forbidden(self):
        self.client.force_login(self.other_manager.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_with_valid_manager(self):
        self.client.force_login(self.manager.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        assessment_enrollments = response.context['assessment_enrollments']

        self.assertEqual(len(assessment_enrollments), 0)

        # Add enrollments
        first_enrollment: AssessmentEnrollment = AssessmentEnrollmentFactory(
            session=Session.SEPTEMBER.name,
            course__parcours_doctoral=self.doctorate,
            course__learning_unit_year__academic_year__year=2020,
        )
        second_enrollment: AssessmentEnrollment = AssessmentEnrollmentFactory(
            session=Session.JUNE.name,
            course__parcours_doctoral=self.doctorate,
            course__learning_unit_year__academic_year__year=2020,
        )
        third_enrollment: AssessmentEnrollment = AssessmentEnrollmentFactory(
            session=Session.JANUARY.name,
            course__parcours_doctoral=self.doctorate,
            course__learning_unit_year__academic_year__year=2020,
        )
        fourth_enrollment: AssessmentEnrollment = AssessmentEnrollmentFactory(
            session=Session.JANUARY.name,
            course__parcours_doctoral=self.doctorate,
            course__learning_unit_year__academic_year__year=2021,
            course__learning_unit_year__acronym='DEF',
            status=StatutInscriptionEvaluation.DESINSCRITE.name,
        )
        fifth_enrollment: AssessmentEnrollment = AssessmentEnrollmentFactory(
            session=Session.JANUARY.name,
            course__parcours_doctoral=self.doctorate,
            course__learning_unit_year__academic_year__year=2021,
            course__learning_unit_year__acronym='ABCD',
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        assessment_enrollments: Dict[int, Dict[str, List[InscriptionEvaluationDTO]]] = response.context[
            'assessment_enrollments'
        ]
        self.assertEqual(len(assessment_enrollments), 2)

        self.assertEqual([2020, 2021], list(assessment_enrollments.keys()))

        # Check 2020 enrollments
        self.assertEqual(len(assessment_enrollments[2020]), 3)

        self.assertEqual(
            [Session.JANUARY.name, Session.JUNE.name, Session.SEPTEMBER.name],
            list(assessment_enrollments[2020].keys()),
        )

        self.assertEqual(len(assessment_enrollments[2020][Session.JANUARY.name]), 1)
        self.assertEqual(len(assessment_enrollments[2020][Session.JUNE.name]), 1)
        self.assertEqual(len(assessment_enrollments[2020][Session.SEPTEMBER.name]), 1)

        # The enrollments are sorted by year, session and acronym
        third_enrollment_dto = assessment_enrollments[2020][Session.JANUARY.name][0]
        second_enrollment_dto = assessment_enrollments[2020][Session.JUNE.name][0]
        first_enrollment_dto = assessment_enrollments[2020][Session.SEPTEMBER.name][0]

        self.assertEqual(first_enrollment_dto.uuid, str(first_enrollment.uuid))
        self.assertEqual(first_enrollment_dto.uuid_activite, str(first_enrollment.course.uuid))
        self.assertEqual(first_enrollment_dto.session, first_enrollment.session)
        self.assertEqual(first_enrollment_dto.statut, first_enrollment.status)
        self.assertEqual(first_enrollment_dto.inscription_tardive, first_enrollment.late_enrollment)
        self.assertEqual(
            first_enrollment_dto.code_unite_enseignement,
            first_enrollment.course.learning_unit_year.acronym,
        )
        self.assertEqual(
            first_enrollment_dto.intitule_unite_enseignement,
            first_enrollment.course.learning_unit_year.complete_title_i18n,
        )
        self.assertEqual(
            first_enrollment_dto.annee_unite_enseignement,
            first_enrollment.course.learning_unit_year.academic_year.year,
        )

        self.assertEqual(second_enrollment_dto.uuid, str(second_enrollment.uuid))
        self.assertEqual(third_enrollment_dto.uuid, str(third_enrollment.uuid))

        # Check 2021 enrollments
        self.assertEqual([Session.JANUARY.name], list(assessment_enrollments[2021].keys()))

        self.assertEqual(len(assessment_enrollments[2021][Session.JANUARY.name]), 2)

        # The enrollments are sorted by year, session and acronym
        fifth_enrollment_dto = assessment_enrollments[2021][Session.JANUARY.name][0]
        fourth_enrollment_dto = assessment_enrollments[2021][Session.JANUARY.name][1]

        self.assertEqual(fifth_enrollment_dto.uuid, str(fifth_enrollment.uuid))
        self.assertTrue(fifth_enrollment_dto.est_acceptee)
        self.assertFalse(fifth_enrollment_dto.est_annulee)
        self.assertEqual(fourth_enrollment_dto.uuid, str(fourth_enrollment.uuid))
        self.assertFalse(fourth_enrollment_dto.est_acceptee)
        self.assertTrue(fourth_enrollment_dto.est_annulee)
