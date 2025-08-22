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
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from base.models.enums.entity_type import EntityType
from base.tests import QueriesAssertionsMixin
from base.tests.factories.entity_version import EntityVersionFactory
from parcours_doctoral.ddd.formation.domain.model.enums import (
    ContexteFormation,
)
from parcours_doctoral.models.activity import Activity
from parcours_doctoral.models.cdd_config import CddConfiguration
from parcours_doctoral.tests.factories.activity import (
    UclCourseFactory,
    UclCourseWithClassFactory,
)
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.supervision import PromoterFactory


@override_settings(WAFFLE_CREATE_MISSING_SWITCHES=False)
class TrainingApiForUCLCourseTestCase(QueriesAssertionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.valid_data_for_ucl_course = {
            'object_type': 'Conference',
            'context': ContexteFormation.DOCTORAL_TRAINING.name,
            'ects': "0.0",
            'category': 'CONFERENCE',
            'parent': None,
            'type': 'A great conference',
            'title': '',
            'participating_proof': [],
            'comment': '',
            'hour_volume': '3',
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

        cls.training_base_url = 'parcours_doctoral_api_v1:doctoral-training'
        cls.url = resolve_url(cls.training_base_url, uuid=cls.parcours_doctoral.uuid)
        cls.complementary_base_url = 'parcours_doctoral_api_v1:complementary-training'
        cls.complementary_url = resolve_url(cls.complementary_base_url, uuid=cls.parcours_doctoral.uuid)
        cls.enrollment_base_url = 'parcours_doctoral_api_v1:course-enrollment'
        cls.enrollment_url = resolve_url(cls.enrollment_base_url, uuid=cls.parcours_doctoral.uuid)

    def test_training_context_with_learning_unit_year(self):
        self.client.force_authenticate(user=self.student.user)

        ucl_course: Activity = UclCourseFactory(
            parcours_doctoral=self.parcours_doctoral,
            context=ContexteFormation.DOCTORAL_TRAINING.name,
        )

        with self.assertNumQueriesLessThan(7, verbose=True):
            response = self.client.get(self.url)

        activities = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(activities), 0)

        ucl_course.course_completed = True
        ucl_course.save()

        with self.assertNumQueriesLessThan(7, verbose=True):
            response = self.client.get(self.url)

        activities = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(activities), 1)

        activity = activities[0]
        self.assertEqual(activity['object_type'], 'UclCourse')
        self.assertEqual(activity['uuid'], str(ucl_course.uuid))
        self.assertEqual(activity['category'], ucl_course.category)
        self.assertEqual(activity['status'], ucl_course.status)
        self.assertEqual(activity['context'], ucl_course.context)
        self.assertEqual(activity['reference_promoter_assent'], ucl_course.reference_promoter_assent)
        self.assertEqual(activity['reference_promoter_comment'], ucl_course.reference_promoter_comment)
        self.assertEqual(activity['cdd_comment'], ucl_course.cdd_comment)
        self.assertEqual(activity['can_be_submitted'], True)
        self.assertEqual(activity['learning_unit_or_class_year'], ucl_course.learning_unit_year.acronym)
        self.assertEqual(
            activity['learning_unit_or_class_year_title'],
            ucl_course.learning_unit_year.learning_container_year.common_title
            + ' - '
            + ucl_course.learning_unit_year.specific_title,
        )
        self.assertEqual(activity['ects'], ucl_course.ects)
        self.assertEqual(activity['academic_year'], ucl_course.learning_unit_year.academic_year.year)
        self.assertEqual(activity['authors'], ucl_course.authors)
        self.assertEqual(activity['hour_volume'], ucl_course.hour_volume)
        self.assertEqual(activity['participating_proof'], ucl_course.participating_proof)

    def test_complementary_training_context_with_learning_unit_year(self):
        self.client.force_authenticate(user=self.student.user)

        ucl_course: Activity = UclCourseFactory(
            parcours_doctoral=self.parcours_doctoral,
            context=ContexteFormation.COMPLEMENTARY_TRAINING.name,
        )

        with self.assertNumQueriesLessThan(7, verbose=True):
            response = self.client.get(self.url)

        activities = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(activities), 0)

        ucl_course.course_completed = True
        ucl_course.save()

        self.student.language = settings.LANGUAGE_CODE_EN
        self.student.save()
        with self.assertNumQueriesLessThan(8):
            response = self.client.get(self.complementary_url, HTTP_ACCEPT_LANGUAGE=settings.LANGUAGE_CODE_EN)

        activities = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(activities), 1)

        activity = activities[0]

        self.assertEqual(activity['uuid'], str(ucl_course.uuid))
        self.assertEqual(activity['context'], ucl_course.context)
        self.assertEqual(activity['learning_unit_or_class_year'], ucl_course.learning_unit_year.acronym)
        self.assertEqual(
            activity['learning_unit_or_class_year_title'],
            ucl_course.learning_unit_year.learning_container_year.common_title_english
            + ' - '
            + ucl_course.learning_unit_year.specific_title_english,
        )
        self.assertEqual(activity['academic_year'], ucl_course.learning_unit_year.academic_year.year)

    def test_enrollment_context_with_learning_class_year(self):
        self.client.force_authenticate(user=self.student.user)

        ucl_course: Activity = UclCourseWithClassFactory(
            parcours_doctoral=self.parcours_doctoral,
            context=ContexteFormation.COMPLEMENTARY_TRAINING.name,
        )

        learning_unit_year = ucl_course.learning_class_year.learning_component_year.learning_unit_year

        with self.assertNumQueriesLessThan(8):
            response = self.client.get(self.enrollment_url)

        activities = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(activities), 1)

        activity = activities[0]

        self.assertEqual(activity['uuid'], str(ucl_course.uuid))
        self.assertEqual(activity['context'], ucl_course.context)
        self.assertEqual(
            activity['learning_unit_or_class_year'],
            learning_unit_year.acronym + '-' + ucl_course.learning_class_year.acronym,
        )
        self.assertEqual(
            activity['learning_unit_or_class_year_title'],
            learning_unit_year.learning_container_year.common_title + ' - ' + ucl_course.learning_class_year.title_fr,
        )
        self.assertEqual(activity['academic_year'], learning_unit_year.academic_year.year)

        ucl_course.completed_course = True
        ucl_course.save()

        with self.assertNumQueriesLessThan(8):
            response = self.client.get(self.enrollment_url, HTTP_ACCEPT_LANGUAGE=settings.LANGUAGE_CODE_EN)

        activities = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(activities), 1)

        activity = activities[0]

        self.assertEqual(activity['uuid'], str(ucl_course.uuid))
        self.assertEqual(activity['context'], ucl_course.context)
        self.assertEqual(
            activity['learning_unit_or_class_year'],
            learning_unit_year.acronym + '-' + ucl_course.learning_class_year.acronym,
        )
        self.assertEqual(
            activity['learning_unit_or_class_year_title'],
            learning_unit_year.learning_container_year.common_title_english
            + ' - '
            + ucl_course.learning_class_year.title_en,
        )
        self.assertEqual(activity['academic_year'], learning_unit_year.academic_year.year)
