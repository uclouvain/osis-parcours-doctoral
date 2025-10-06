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
import uuid

import freezegun
from django.shortcuts import resolve_url
from rest_framework import status
from rest_framework.test import APITestCase

from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from deliberation.models.enums.numero_session import Session
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.formation.domain.validator.exceptions import (
    InscriptionEvaluationNonTrouveeException,
)
from parcours_doctoral.tests.factories.assessment_enrollment import (
    AssessmentEnrollmentFactory,
    AssessmentEnrollmentForClassFactory,
)
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.roles import StudentRoleFactory
from parcours_doctoral.tests.factories.supervision import (
    CaMemberFactory,
    PromoterFactory,
)


@freezegun.freeze_time('2023-01-01')
class AssessmentEnrollmentListViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Users
        cls.student = StudentRoleFactory().person
        cls.other_student = StudentRoleFactory().person
        cls.no_role_user = PersonFactory().user
        promoter = PromoterFactory()
        cls.process = promoter.process
        cls.promoter_user = promoter.person.user
        cls.committee_member_user = CaMemberFactory(process=cls.process).person.user
        cls.base_namespace = 'parcours_doctoral_api_v1:assessment-enrollment-list'

    def setUp(self):
        self.doctorate = ParcoursDoctoralFactory(
            supervision_group=self.process,
            student=self.student,
        )
        self.url = resolve_url(self.base_namespace, uuid=self.doctorate.uuid)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.student.user)
        methods_not_allowed = [
            'delete',
            'patch',
            'post',
            'put',
        ]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_assessment_enrollments_with_user_not_logged_is_forbidden(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_assessment_enrollments_with_user_with_no_role_is_forbidden(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_assessment_enrollments_with_invalid_enrolment_is_forbidden(self):
        in_creation_doctorate = ParcoursDoctoralFactory(
            supervision_group=self.doctorate.supervision_group,
            student=self.student,
            status=ChoixStatutParcoursDoctoral.ADMIS.name,
            create_student__with_valid_enrolment=False,
        )

        url = resolve_url(self.base_namespace, uuid=in_creation_doctorate.uuid)

        users = [
            self.promoter_user,
            self.committee_member_user,
            self.student.user,
        ]

        for user in users:
            self.client.force_authenticate(user=user)
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_assessment_enrollments_with_student(self):
        self.client.force_authenticate(user=self.student.user)

        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()
        self.assertEqual(len(json_response), 0)

        # Add enrollments

        first_enrollment = AssessmentEnrollmentFactory(
            session=Session.JANUARY.name,
            course__parcours_doctoral=self.doctorate,
            course__learning_unit_year__academic_year__year=2020,
        )
        second_enrollment = AssessmentEnrollmentForClassFactory(
            session=Session.JUNE.name,
            course__parcours_doctoral=self.doctorate,
            course__learning_class_year__learning_component_year__learning_unit_year__academic_year__year=2020,
        )
        second_learning_unit_year = (
            second_enrollment.course.learning_class_year.learning_component_year.learning_unit_year
        )
        third_enrollment = AssessmentEnrollmentFactory(
            session=Session.SEPTEMBER.name,
            course__parcours_doctoral=self.doctorate,
            course__learning_unit_year__academic_year__year=2020,
        )
        fourth_enrollment = AssessmentEnrollmentFactory(
            session=Session.JANUARY.name,
            course__parcours_doctoral=self.doctorate,
            course__learning_unit_year__academic_year__year=2021,
        )

        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()
        self.assertEqual(len(json_response), 4)

        self.assertEqual(json_response[0]['uuid'], str(first_enrollment.uuid))
        self.assertEqual(json_response[0]['uuid_activite'], str(first_enrollment.course.uuid))
        self.assertEqual(json_response[0]['session'], first_enrollment.session)
        self.assertEqual(json_response[0]['statut'], first_enrollment.status)
        self.assertEqual(json_response[0]['inscription_tardive'], first_enrollment.late_enrollment)
        self.assertEqual(json_response[0]['desinscription_tardive'], first_enrollment.late_unenrollment)
        self.assertEqual(
            json_response[0]['code_unite_enseignement'],
            first_enrollment.course.learning_unit_year.acronym,
        )
        self.assertEqual(
            json_response[0]['intitule_unite_enseignement'],
            first_enrollment.course.learning_unit_year.complete_title_i18n,
        )
        self.assertEqual(
            json_response[0]['annee_unite_enseignement'],
            first_enrollment.course.learning_unit_year.academic_year.year,
        )

        self.assertEqual(json_response[1]['uuid'], str(second_enrollment.uuid))
        self.assertEqual(
            json_response[1]['code_unite_enseignement'],
            second_learning_unit_year.acronym + '-' + second_enrollment.course.learning_class_year.acronym,
        )
        self.assertEqual(
            json_response[1]['intitule_unite_enseignement'],
            second_learning_unit_year.learning_container_year.common_title
            + ' - '
            + second_enrollment.course.learning_class_year.title_fr,
        )
        self.assertEqual(
            json_response[1]['annee_unite_enseignement'],
            second_learning_unit_year.academic_year.year,
        )
        self.assertEqual(json_response[2]['uuid'], str(third_enrollment.uuid))
        self.assertEqual(json_response[3]['uuid'], str(fourth_enrollment.uuid))


@freezegun.freeze_time('2023-01-01')
class AssessmentEnrollmentDetailViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Users
        cls.student = StudentRoleFactory().person
        cls.other_student = StudentRoleFactory().person
        cls.no_role_user = PersonFactory().user
        promoter = PromoterFactory()
        cls.process = promoter.process
        cls.promoter_user = promoter.person.user
        cls.committee_member_user = CaMemberFactory(process=cls.process).person.user
        cls.base_namespace = 'parcours_doctoral_api_v1:assessment-enrollment-detail'
        cls.doctorate = ParcoursDoctoralFactory(
            supervision_group=cls.process,
            student=cls.student,
        )
        cls.enrollment = AssessmentEnrollmentFactory(
            course__parcours_doctoral=cls.doctorate,
        )
        cls.url = resolve_url(cls.base_namespace, uuid=cls.doctorate.uuid, enrollment_uuid=cls.enrollment.uuid)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.student.user)
        methods_not_allowed = [
            'delete',
            'patch',
            'post',
            'put',
        ]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_assessment_enrollment_with_user_not_logged_is_forbidden(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_assessment_enrollment_with_user_with_no_role_is_forbidden(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_assessment_enrollment_with_invalid_enrolment_is_forbidden(self):
        in_creation_doctorate = ParcoursDoctoralFactory(
            supervision_group=self.doctorate.supervision_group,
            student=self.student,
            create_student__with_valid_enrolment=False,
        )

        enrollment = AssessmentEnrollmentFactory(
            course__parcours_doctoral=in_creation_doctorate,
        )

        url = resolve_url(self.base_namespace, uuid=in_creation_doctorate.uuid, enrollment_uuid=enrollment.uuid)

        users = [
            self.promoter_user,
            self.committee_member_user,
            self.student.user,
        ]

        for user in users:
            self.client.force_authenticate(user=user)
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_unknown_assessment_enrollment(self):
        self.client.force_authenticate(user=self.student.user)

        url = resolve_url(self.base_namespace, uuid=self.doctorate.uuid, enrollment_uuid=uuid.uuid4())

        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        exception = InscriptionEvaluationNonTrouveeException()
        self.assertIn(
            {'status_code': exception.status_code, 'detail': exception.message},
            response.json().get('non_field_errors', []),
        )

    def test_get_assessment_enrollment_with_student(self):
        self.client.force_authenticate(user=self.student.user)

        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()

        self.assertEqual(json_response['uuid'], str(self.enrollment.uuid))
        self.assertEqual(json_response['uuid_activite'], str(self.enrollment.course.uuid))
        self.assertEqual(json_response['session'], self.enrollment.session)
        self.assertEqual(json_response['statut'], self.enrollment.status)
        self.assertEqual(json_response['inscription_tardive'], self.enrollment.late_enrollment)
        self.assertEqual(json_response['code_unite_enseignement'], self.enrollment.course.learning_unit_year.acronym)
        self.assertEqual(
            json_response['intitule_unite_enseignement'],
            self.enrollment.course.learning_unit_year.complete_title_i18n,
        )
        self.assertEqual(
            json_response['annee_unite_enseignement'],
            self.enrollment.course.learning_unit_year.academic_year.year,
        )

    def test_get_assessment_enrollment_for_class_with_student(self):
        self.client.force_authenticate(user=self.student.user)

        class_enrollment = AssessmentEnrollmentForClassFactory(
            session=Session.JUNE.name,
            course__parcours_doctoral=self.doctorate,
            course__learning_class_year__learning_component_year__learning_unit_year__academic_year__year=2020,
        )
        second_learning_unit_year = (
            class_enrollment.course.learning_class_year.learning_component_year.learning_unit_year
        )
        url = resolve_url(self.base_namespace, uuid=self.doctorate.uuid, enrollment_uuid=class_enrollment.uuid)

        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()

        self.assertEqual(
            json_response['code_unite_enseignement'],
            second_learning_unit_year.acronym + '-' + class_enrollment.course.learning_class_year.acronym,
        )
        self.assertEqual(
            json_response['intitule_unite_enseignement'],
            second_learning_unit_year.learning_container_year.common_title
            + ' - '
            + class_enrollment.course.learning_class_year.title_fr,
        )
        self.assertEqual(
            json_response['annee_unite_enseignement'],
            second_learning_unit_year.academic_year.year,
        )
