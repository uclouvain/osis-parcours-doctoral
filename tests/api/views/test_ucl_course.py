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
import decimal

from django.conf import settings
from django.shortcuts import resolve_url
from django.test import override_settings
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.test import APITestCase

from base.models.enums.entity_type import EntityType
from base.tests import QueriesAssertionsMixin
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from learning_unit.tests.factories.learning_class_year import (
    LearningClassLecturingFactory,
)
from parcours_doctoral.ddd.formation.domain.model.enums import (
    CategorieActivite,
    ContexteFormation,
    StatutActivite,
)
from parcours_doctoral.models.activity import Activity
from parcours_doctoral.models.cdd_config import CddConfiguration
from parcours_doctoral.tests.factories.activity import (
    UclCourseFactory,
    UclCourseWithClassFactory,
)
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.supervision import PromoterFactory


class TrainingApiForUCLCourseBaseTestCase(QueriesAssertionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
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


@override_settings(WAFFLE_CREATE_MISSING_SWITCHES=False)
class ListTrainingApiForUCLCourseTestCase(TrainingApiForUCLCourseBaseTestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.training_base_url = 'parcours_doctoral_api_v1:doctoral-training'
        cls.complementary_base_url = 'parcours_doctoral_api_v1:complementary-training'
        cls.enrollment_base_url = 'parcours_doctoral_api_v1:course-enrollment'
        cls.url = resolve_url(cls.training_base_url, uuid=cls.parcours_doctoral.uuid)
        cls.complementary_url = resolve_url(cls.complementary_base_url, uuid=cls.parcours_doctoral.uuid)
        cls.enrollment_url = resolve_url(cls.enrollment_base_url, uuid=cls.parcours_doctoral.uuid)

    def test_training_context_with_learning_unit_year(self):
        self.client.force_authenticate(user=self.student.user)

        ucl_course: Activity = UclCourseFactory(
            parcours_doctoral=self.parcours_doctoral,
            context=ContexteFormation.DOCTORAL_TRAINING.name,
        )

        with self.assertNumQueriesLessThan(8, verbose=True):
            response = self.client.get(self.url)

        activities = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(activities), 0)

        ucl_course.course_completed = True
        ucl_course.save()

        with self.assertNumQueriesLessThan(8, verbose=True):
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
        self.assertEqual(activity['course'], ucl_course.learning_unit_year.acronym)
        self.assertEqual(
            activity['course_title'],
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

        with self.assertNumQueriesLessThan(8, verbose=True):
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
        self.assertEqual(activity['course'], ucl_course.learning_unit_year.acronym)
        self.assertEqual(
            activity['course_title'],
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
            activity['course'],
            learning_unit_year.acronym + '-' + ucl_course.learning_class_year.acronym,
        )
        self.assertEqual(
            activity['course_title'],
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
            activity['course'],
            learning_unit_year.acronym + '-' + ucl_course.learning_class_year.acronym,
        )
        self.assertEqual(
            activity['course_title'],
            learning_unit_year.learning_container_year.common_title_english
            + ' - '
            + ucl_course.learning_class_year.title_en,
        )
        self.assertEqual(activity['academic_year'], learning_unit_year.academic_year.year)


@override_settings(WAFFLE_CREATE_MISSING_SWITCHES=False)
class SingleTrainingApiForUCLCourseTestCase(TrainingApiForUCLCourseBaseTestCase):
    def setUp(self):
        self.ucl_course: Activity = UclCourseFactory(
            parcours_doctoral=self.parcours_doctoral,
            context=ContexteFormation.DOCTORAL_TRAINING.name,
            reference_promoter_assent=True,
            reference_promoter_comment='Promoter comment',
            cdd_comment='Cdd comment',
            ects=decimal.Decimal(10.2),
            authors='John Doe',
            hour_volume='10',
            participating_proof=[],
        )
        self.url = resolve_url(
            'parcours_doctoral_api_v1:training', uuid=self.parcours_doctoral.uuid, activity_id=self.ucl_course.uuid
        )

    def test_training_context_with_learning_unit_year(self):
        self.client.force_authenticate(user=self.student.user)

        self.ucl_course.context = ContexteFormation.DOCTORAL_TRAINING.name
        self.ucl_course.save()

        with self.assertNumQueriesLessThan(8, verbose=True):
            response = self.client.get(self.url)

        activity = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(activity['object_type'], 'UclCourse')
        self.assertEqual(activity['uuid'], str(self.ucl_course.uuid))
        self.assertEqual(activity['category'], self.ucl_course.category)
        self.assertEqual(activity['status'], self.ucl_course.status)
        self.assertEqual(activity['context'], self.ucl_course.context)
        self.assertEqual(activity['reference_promoter_assent'], self.ucl_course.reference_promoter_assent)
        self.assertEqual(activity['reference_promoter_comment'], self.ucl_course.reference_promoter_comment)
        self.assertEqual(activity['cdd_comment'], self.ucl_course.cdd_comment)
        self.assertEqual(activity['can_be_submitted'], True)
        self.assertEqual(activity['course'], self.ucl_course.learning_unit_year.acronym)
        self.assertEqual(
            activity['course_title'],
            self.ucl_course.learning_unit_year.learning_container_year.common_title
            + ' - '
            + self.ucl_course.learning_unit_year.specific_title,
        )
        self.assertEqual(activity['ects'], self.ucl_course.ects)
        self.assertEqual(activity['academic_year'], self.ucl_course.learning_unit_year.academic_year.year)
        self.assertEqual(activity['authors'], self.ucl_course.authors)
        self.assertEqual(activity['hour_volume'], self.ucl_course.hour_volume)
        self.assertEqual(activity['participating_proof'], self.ucl_course.participating_proof)

    def test_complementary_training_context_with_learning_unit_year(self):
        self.client.force_authenticate(user=self.student.user)

        self.ucl_course.context = ContexteFormation.COMPLEMENTARY_TRAINING.name
        self.ucl_course.save()

        self.student.language = settings.LANGUAGE_CODE_EN
        self.student.save()
        with self.assertNumQueriesLessThan(9):
            response = self.client.get(self.url, HTTP_ACCEPT_LANGUAGE=settings.LANGUAGE_CODE_EN)

        activity = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(activity['uuid'], str(self.ucl_course.uuid))
        self.assertEqual(activity['context'], self.ucl_course.context)
        self.assertEqual(activity['course'], self.ucl_course.learning_unit_year.acronym)
        self.assertEqual(
            activity['course_title'],
            self.ucl_course.learning_unit_year.learning_container_year.common_title_english
            + ' - '
            + self.ucl_course.learning_unit_year.specific_title_english,
        )
        self.assertEqual(activity['academic_year'], self.ucl_course.learning_unit_year.academic_year.year)

    def test_enrollment_context_with_learning_class_year(self):
        self.client.force_authenticate(user=self.student.user)

        self.ucl_course.learning_unit_year = None
        self.ucl_course.learning_class_year = LearningClassLecturingFactory()
        self.ucl_course.save()
        learning_unit_year = self.ucl_course.learning_class_year.learning_component_year.learning_unit_year

        with self.assertNumQueriesLessThan(8):
            response = self.client.get(self.url)

        activity = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(activity['context'], self.ucl_course.context)
        self.assertEqual(
            activity['course'],
            learning_unit_year.acronym + '-' + self.ucl_course.learning_class_year.acronym,
        )
        self.assertEqual(
            activity['course_title'],
            learning_unit_year.learning_container_year.common_title
            + ' - '
            + self.ucl_course.learning_class_year.title_fr,
        )
        self.assertEqual(activity['academic_year'], learning_unit_year.academic_year.year)


@override_settings(WAFFLE_CREATE_MISSING_SWITCHES=False)
class SingleUpdateTrainingApiForUCLCourseTestCase(TrainingApiForUCLCourseBaseTestCase):
    def setUp(self):
        self.ucl_course: Activity = UclCourseFactory(
            parcours_doctoral=self.parcours_doctoral,
            context=ContexteFormation.DOCTORAL_TRAINING.name,
            reference_promoter_assent=True,
            reference_promoter_comment='Promoter comment',
            cdd_comment='Cdd comment',
            ects=decimal.Decimal(10.2),
            authors='John Doe',
            hour_volume='10',
            participating_proof=[],
        )
        self.url = resolve_url(
            'parcours_doctoral_api_v1:training',
            uuid=self.parcours_doctoral.uuid,
            activity_id=self.ucl_course.uuid,
        )

    def test_with_invalid_data(self):
        self.client.force_authenticate(user=self.student.user)

        default_data = {
            'category': CategorieActivite.UCL_COURSE.name,
            'context': ContexteFormation.COMPLEMENTARY_TRAINING.name,
            'object_type': CategorieActivite.UCL_COURSE.name,
        }

        new_learning_unit_year = LearningUnitYearFactory(academic_year__current=True)

        academic_year = new_learning_unit_year.academic_year.year

        self.parcours_doctoral.training.management_entity.doctorate_config.is_complementary_training_enabled = False
        self.parcours_doctoral.training.management_entity.doctorate_config.save()

        response = self.client.put(self.url, data=default_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        json_response = response.json()

        self.assertIn(_('Please choose a correct academic year.'), json_response.get('academic_year', []))
        self.assertIn(_('Please choose a correct learning unit.'), json_response.get('course', []))

        response = self.client.put(
            self.url,
            data={
                **default_data,
                'course': new_learning_unit_year.acronym,
                'academic_year': academic_year + 2,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        json_response = response.json()

        self.assertIn(_('Please choose a correct academic year.'), json_response.get('academic_year', []))

        response = self.client.put(
            self.url,
            data={
                **default_data,
                'course': 'UNKNOWN',
                'academic_year': academic_year,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        json_response = response.json()

        self.assertIn(
            _('No element has been found for the academic year %(academic_year)s.')
            % {'academic_year': f'{academic_year}-{academic_year + 1}'},
            json_response.get('course', []),
        )

        response = self.client.put(
            self.url,
            data={
                **default_data,
                'course': f'{new_learning_unit_year.acronym}-1',
                'academic_year': academic_year,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        json_response = response.json()

        self.assertIn(
            _('No element has been found for the academic year %(academic_year)s.')
            % {'academic_year': f'{academic_year}-{academic_year + 1}'},
            json_response.get('course', []),
        )

        LearningClassLecturingFactory(learning_component_year__learning_unit_year=new_learning_unit_year)

        response = self.client.put(
            self.url,
            data={
                **default_data,
                'course': new_learning_unit_year.acronym,
                'academic_year': academic_year,
            },
        )

        json_response = response.json()

        self.assertIn(
            _('At least one class exists for this learning unit. Please select it instead of the learning unit.'),
            json_response.get('course', []),
        )

    def test_update_with_learning_unit_year(self):
        self.client.force_authenticate(user=self.student.user)

        new_learning_unit_year = LearningUnitYearFactory(academic_year__current=True)

        response = self.client.put(
            self.url,
            data={
                'course': new_learning_unit_year.acronym,
                'academic_year': new_learning_unit_year.academic_year.year,
                'category': self.ucl_course.category,
                'context': ContexteFormation.COMPLEMENTARY_TRAINING.name,
            },
        )

        activity = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(activity['object_type'], 'UclCourse')
        self.assertEqual(activity['uuid'], str(self.ucl_course.uuid))
        self.assertEqual(activity['category'], self.ucl_course.category)
        self.assertEqual(activity['status'], self.ucl_course.status)
        self.assertEqual(activity['context'], ContexteFormation.COMPLEMENTARY_TRAINING.name)
        self.assertEqual(activity['reference_promoter_assent'], self.ucl_course.reference_promoter_assent)
        self.assertEqual(activity['reference_promoter_comment'], self.ucl_course.reference_promoter_comment)
        self.assertEqual(activity['cdd_comment'], self.ucl_course.cdd_comment)
        self.assertEqual(activity['can_be_submitted'], True)
        self.assertEqual(activity['course'], new_learning_unit_year.acronym)
        self.assertEqual(
            activity['course_title'],
            new_learning_unit_year.learning_container_year.common_title + ' - ' + new_learning_unit_year.specific_title,
        )
        self.assertEqual(activity['ects'], self.ucl_course.ects)
        self.assertEqual(activity['academic_year'], new_learning_unit_year.academic_year.year)
        self.assertEqual(activity['authors'], self.ucl_course.authors)
        self.assertEqual(activity['hour_volume'], self.ucl_course.hour_volume)
        self.assertEqual(activity['participating_proof'], self.ucl_course.participating_proof)

        self.ucl_course.refresh_from_db()
        self.assertEqual(self.ucl_course.learning_unit_year, new_learning_unit_year)
        self.assertEqual(self.ucl_course.learning_class_year, None)

    def test_update_with_learning_class_year(self):
        self.client.force_authenticate(user=self.student.user)

        new_learning_class_year = LearningClassLecturingFactory(
            learning_component_year__learning_unit_year__academic_year__current=True,
        )
        learning_unit_year = new_learning_class_year.learning_component_year.learning_unit_year

        response = self.client.put(
            self.url,
            data={
                'course': learning_unit_year.acronym + '-' + new_learning_class_year.acronym,
                'academic_year': learning_unit_year.academic_year.year,
                'category': self.ucl_course.category,
                'context': ContexteFormation.COMPLEMENTARY_TRAINING.name,
            },
        )

        activity = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(activity['context'], ContexteFormation.COMPLEMENTARY_TRAINING.name)
        self.assertEqual(
            activity['course'],
            learning_unit_year.acronym + '-' + new_learning_class_year.acronym,
        )
        self.assertEqual(
            activity['course_title'],
            learning_unit_year.learning_container_year.common_title + ' - ' + new_learning_class_year.title_fr,
        )
        self.assertEqual(activity['academic_year'], learning_unit_year.academic_year.year)
        self.assertEqual(activity['context'], ContexteFormation.COMPLEMENTARY_TRAINING.name)

        self.ucl_course.refresh_from_db()
        self.assertEqual(self.ucl_course.learning_unit_year, None)
        self.assertEqual(self.ucl_course.learning_class_year, new_learning_class_year)


@override_settings(WAFFLE_CREATE_MISSING_SWITCHES=False)
class SingleCreateTrainingApiForUCLCourseTestCase(TrainingApiForUCLCourseBaseTestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.enrollment_base_url = 'parcours_doctoral_api_v1:doctoral-training'
        # cls.enrollment_base_url = 'parcours_doctoral_api_v1:course-enrollment'
        cls.url = resolve_url(cls.enrollment_base_url, uuid=cls.parcours_doctoral.uuid)

    def test_update_with_learning_unit_year(self):
        self.client.force_authenticate(user=self.student.user)

        new_learning_unit_year = LearningUnitYearFactory(academic_year__current=True)

        response = self.client.post(
            self.url,
            data={
                'course': new_learning_unit_year.acronym,
                'academic_year': new_learning_unit_year.academic_year.year,
                'category': CategorieActivite.UCL_COURSE.name,
                'context': ContexteFormation.DOCTORAL_TRAINING.name,
            },
        )

        activity = response.json()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(activity['object_type'], 'UclCourse')
        self.assertEqual(activity['category'], CategorieActivite.UCL_COURSE.name)
        self.assertEqual(activity['status'], StatutActivite.NON_SOUMISE.name)
        self.assertEqual(activity['context'], ContexteFormation.DOCTORAL_TRAINING.name)
        self.assertEqual(activity['reference_promoter_assent'], None)
        self.assertEqual(activity['reference_promoter_comment'], '')
        self.assertEqual(activity['cdd_comment'], '')
        self.assertEqual(activity['course'], new_learning_unit_year.acronym)
        self.assertEqual(
            activity['course_title'],
            new_learning_unit_year.learning_container_year.common_title + ' - ' + new_learning_unit_year.specific_title,
        )
        self.assertEqual(activity['ects'], 0)
        self.assertEqual(activity['academic_year'], new_learning_unit_year.academic_year.year)
        self.assertEqual(activity['authors'], '')
        self.assertEqual(activity['hour_volume'], '')
        self.assertEqual(activity['participating_proof'], [])

        ucl_course = Activity.objects.filter(uuid=activity['uuid'], parcours_doctoral=self.parcours_doctoral).first()

        self.assertIsNotNone(ucl_course)
        self.assertEqual(ucl_course.learning_unit_year, new_learning_unit_year)
        self.assertEqual(ucl_course.learning_class_year, None)

    def test_update_with_learning_class_year(self):
        self.client.force_authenticate(user=self.student.user)

        new_learning_class_year = LearningClassLecturingFactory(
            learning_component_year__learning_unit_year__academic_year__current=True,
        )
        learning_unit_year = new_learning_class_year.learning_component_year.learning_unit_year

        response = self.client.post(
            self.url,
            data={
                'course': learning_unit_year.acronym + '-' + new_learning_class_year.acronym,
                'academic_year': learning_unit_year.academic_year.year,
                'category': CategorieActivite.UCL_COURSE.name,
                'context': ContexteFormation.COMPLEMENTARY_TRAINING.name,
            },
        )

        activity = response.json()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(activity['context'], ContexteFormation.COMPLEMENTARY_TRAINING.name)
        self.assertEqual(
            activity['course'],
            learning_unit_year.acronym + '-' + new_learning_class_year.acronym,
        )
        self.assertEqual(
            activity['course_title'],
            learning_unit_year.learning_container_year.common_title + ' - ' + new_learning_class_year.title_fr,
        )
        self.assertEqual(activity['academic_year'], learning_unit_year.academic_year.year)
        self.assertEqual(activity['context'], ContexteFormation.COMPLEMENTARY_TRAINING.name)

        ucl_course = Activity.objects.filter(uuid=activity['uuid'], parcours_doctoral=self.parcours_doctoral).first()

        self.assertIsNotNone(ucl_course)
        self.assertEqual(ucl_course.learning_unit_year, None)
        self.assertEqual(ucl_course.learning_class_year, new_learning_class_year)
