# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from base.models.enums.entity_type import EntityType
from base.tests import QueriesAssertionsMixin
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from django.shortcuts import resolve_url
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.formation.domain.model.enums import (
    CategorieActivite,
    ContexteFormation,
    StatutActivite,
)
from parcours_doctoral.models.activity import Activity
from parcours_doctoral.models.cdd_config import CddConfiguration
from parcours_doctoral.tests.factories.activity import (
    ActivityFactory,
    ConferenceCommunicationFactory,
    ConferenceFactory,
    CourseFactory,
    ServiceFactory,
    UclCourseFactory,
)
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.roles import StudentRoleFactory
from parcours_doctoral.tests.factories.supervision import PromoterFactory


@override_settings(WAFFLE_CREATE_MISSING_SWITCHES=False)
class TrainingApiTestCase(QueriesAssertionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.valid_data_for_conference = {
            'object_type': 'Conference',
            'context': ContexteFormation.DOCTORAL_TRAINING.name,
            'ects': "0.0",
            'category': 'CONFERENCE',
            'parent': None,
            'type': 'A great conference',
            'title': '',
            'participating_proof': [],
            'comment': '',
            'start_date': None,
            'end_date': None,
            'participating_days': 0.0,
            'is_online': False,
            'country': None,
            'city': '',
            'organizing_institution': '',
            'website': '',
        }
        cls.commission = EntityVersionFactory(
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        ).entity
        CddConfiguration.objects.create(cdd=cls.commission, is_complementary_training_enabled=True)
        cls.reference_promoter = PromoterFactory(is_reference_promoter=True)
        cls.parcours_doctoral = ParcoursDoctoralFactory(
            training__management_entity=cls.commission,
            supervision_group=cls.reference_promoter.process,
        )
        cls.student = cls.parcours_doctoral.student
        cls.other_student_user = StudentRoleFactory(person__first_name="Jim").person.user
        cls.no_role_user = PersonFactory(first_name="Joe").user
        cls.training_base_url = 'parcours_doctoral_api_v1:doctoral-training'
        cls.url = resolve_url(cls.training_base_url, uuid=cls.parcours_doctoral.uuid)
        cls.activity = ConferenceFactory(parcours_doctoral=cls.parcours_doctoral)
        cls.activity_url = resolve_url(
            "parcours_doctoral_api_v1:training",
            uuid=cls.parcours_doctoral.uuid,
            activity_id=cls.activity.uuid,
        )
        cls.complementary_base_url = 'parcours_doctoral_api_v1:complementary-training'
        cls.complementary_url = resolve_url(cls.complementary_base_url, uuid=cls.parcours_doctoral.uuid)
        cls.enrollment_base_url = 'parcours_doctoral_api_v1:course-enrollment'
        cls.enrollment_url = resolve_url(cls.enrollment_base_url, uuid=cls.parcours_doctoral.uuid)

    def test_user_not_logged_assert_not_authorized(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.student.user)
        methods_not_allowed = ['delete', 'patch', 'put']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_of_in_creation_doctorate_is_forbidden(self):
        self.client.force_authenticate(user=self.student.user)

        in_creation_doctorate = ParcoursDoctoralFactory(
            supervision_group=self.parcours_doctoral.supervision_group,
            student=self.student,
            status=ChoixStatutParcoursDoctoral.EN_COURS_DE_CREATION_PAR_GESTIONNAIRE.name,
        )

        training_url = resolve_url(self.training_base_url, uuid=in_creation_doctorate.uuid)
        complementary_url = resolve_url(self.complementary_base_url, uuid=in_creation_doctorate.uuid)
        enrollment_url = resolve_url(self.enrollment_base_url, uuid=in_creation_doctorate.uuid)

        response = self.client.get(training_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(complementary_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(enrollment_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        in_creation_doctorate.status = ChoixStatutParcoursDoctoral.EN_ATTENTE_INJECTION_EPC.name
        in_creation_doctorate.save()

        response = self.client.get(training_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(complementary_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(enrollment_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_training_get_with_student(self):
        self.client.force_authenticate(user=self.student.user)

        with self.assertNumQueriesLessThan(8):
            response = self.client.get(self.url)
        activities = response.json()
        self.assertEqual(len(activities), 1)

        CourseFactory(parcours_doctoral=self.parcours_doctoral, context=ContexteFormation.COMPLEMENTARY_TRAINING.name)
        with self.assertNumQueriesLessThan(8):
            response = self.client.get(self.complementary_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        activities = response.json()
        self.assertEqual(len(activities), 1)

        UclCourseFactory(parcours_doctoral=self.parcours_doctoral, context=ContexteFormation.FREE_COURSE.name)
        with self.assertNumQueriesLessThan(8):
            response = self.client.get(self.enrollment_url)
        activities = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(activities), 1)

    def test_training_get_with_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_training_get_with_other_student(self):
        self.client.force_authenticate(user=self.other_student_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_training_create_with_student(self):
        self.client.force_authenticate(user=self.student.user)

        response = self.client.post(self.url, self.valid_data_for_conference)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())

    def test_training_create_errors_with_student(self):
        self.client.force_authenticate(user=self.student.user)

        data = {
            **self.valid_data_for_conference,
            'start_date': '02/01/2022',
            'end_date': '01/01/2022',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.json())

    def test_training_create_child_with_student(self):
        self.client.force_authenticate(user=self.student.user)
        data = {
            'object_type': 'ConferenceCommunication',
            'context': ContexteFormation.DOCTORAL_TRAINING.name,
            'ects': 0,
            'category': 'COMMUNICATION',
            'parent': self.activity.uuid,
            'type': 'A great communication',
            'title': '',
            'committee': '',
            'dial_reference': '',
            'comment': '',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())

    def test_training_get_detail_with_student(self):
        self.client.force_authenticate(user=self.student.user)

        response = self.client.get(self.activity_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        subactivity = ActivityFactory(
            parcours_doctoral=self.parcours_doctoral,
            category=CategorieActivite.COMMUNICATION.name,
            parent=self.activity,
        )
        activity_url = resolve_url(
            "parcours_doctoral_api_v1:training", uuid=self.parcours_doctoral.uuid, activity_id=subactivity.uuid
        )
        response = self.client.get(activity_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_training_update_with_student(self):
        self.client.force_authenticate(user=self.student.user)

        data = {
            'object_type': 'Conference',
            'context': ContexteFormation.DOCTORAL_TRAINING.name,
            'ects': "0.0",
            'category': 'CONFERENCE',
            'parent': None,
            'type': 'A great conference',
            'title': '',
            'participating_proof': [],
            'comment': '',
            'start_date': None,
            'end_date': None,
            'participating_days': 0.0,
            'is_online': False,
            'country': None,
            'city': '',
            'organizing_institution': '',
            'website': '',
        }
        response = self.client.put(self.activity_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_training_config(self):
        self.client.force_authenticate(user=self.student.user)
        config_url = resolve_url("parcours_doctoral_api_v1:training-config", uuid=self.parcours_doctoral.uuid)
        response = self.client.get(config_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_training_should_delete_unsubmitted(self):
        service = ServiceFactory(parcours_doctoral=self.parcours_doctoral)
        self.client.force_authenticate(user=self.student.user)
        url = resolve_url(
            "parcours_doctoral_api_v1:training", uuid=self.parcours_doctoral.uuid, activity_id=service.uuid
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(Activity.objects.filter(pk=service.pk).first())

    def test_training_should_not_delete_submitted(self):
        service = ServiceFactory(parcours_doctoral=self.parcours_doctoral, status=StatutActivite.SOUMISE.name)
        self.client.force_authenticate(user=self.student.user)
        url = resolve_url(
            "parcours_doctoral_api_v1:training", uuid=self.parcours_doctoral.uuid, activity_id=service.uuid
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(Activity.objects.filter(pk=service.pk).first())

    def test_training_should_not_delete_parent_with_child_submitted(self):
        communication = ConferenceCommunicationFactory(
            parcours_doctoral=self.parcours_doctoral,
            status=StatutActivite.SOUMISE.name,
        )
        self.client.force_authenticate(user=self.student.user)
        url = resolve_url(
            "parcours_doctoral_api_v1:training", uuid=self.parcours_doctoral.uuid, activity_id=communication.parent.uuid
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(Activity.objects.filter(pk=communication.pk).first())
        self.assertIsNotNone(Activity.objects.filter(pk=communication.parent.pk).first())

    def test_training_should_delete_parent_unsubmitted_with_child(self):
        communication = ConferenceCommunicationFactory(
            parcours_doctoral=self.parcours_doctoral,
            parent=self.activity,
        )
        self.client.force_authenticate(user=self.student.user)
        response = self.client.delete(self.activity_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(Activity.objects.filter(pk__in=[communication.pk, self.activity.pk]).first())

    def test_training_submit(self):
        service = ServiceFactory(parcours_doctoral=self.parcours_doctoral)
        self.client.force_authenticate(user=self.student.user)
        submit_url = resolve_url("parcours_doctoral_api_v1:training-submit", uuid=self.parcours_doctoral.uuid)
        response = self.client.post(submit_url, {'activity_uuids': [service.uuid]})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_training_submit_with_error(self):
        self.client.force_authenticate(user=self.student.user)
        service = ServiceFactory(parcours_doctoral=self.parcours_doctoral, title="")
        submit_url = resolve_url("parcours_doctoral_api_v1:training-submit", uuid=self.parcours_doctoral.uuid)
        response = self.client.post(submit_url, {'activity_uuids': [service.uuid]})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_training_assent(self):
        self.client.force_authenticate(user=self.reference_promoter.person.user)
        submit_url = resolve_url("parcours_doctoral_api_v1:training-assent", uuid=self.parcours_doctoral.uuid)
        data = {
            'approbation': False,
            'commentaire': 'Do not agree',
        }
        response = self.client.post(f"{submit_url}?activity_id={self.activity.uuid}", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.reference_promoter_comment, "Do not agree")
