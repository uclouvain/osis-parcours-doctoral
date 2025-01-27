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

from parcours_doctoral.ddd.formation.domain.model.enums import ContexteFormation, CategorieActivite, StatutActivite
from parcours_doctoral.models import Activity
from parcours_doctoral.tests.factories.activity import ActivityFactory, UclCourseFactory
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory


class ActivityTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.doctorate = ParcoursDoctoralFactory()
        cls.doctorate_uuid = cls.doctorate.uuid

    def test_get_doctoral_training_credits_number(self):
        credits_number = Activity.objects.get_doctoral_training_credits_number(
            parcours_doctoral_uuid=self.doctorate_uuid,
        )

        self.assertEqual(credits_number, 0)

        conference = ActivityFactory(
            parcours_doctoral=self.doctorate,
            context=ContexteFormation.DOCTORAL_TRAINING.name,
            category=CategorieActivite.CONFERENCE.name,
            status=StatutActivite.ACCEPTEE.name,
            ects=10,
        )

        credits_number = Activity.objects.get_doctoral_training_credits_number(
            parcours_doctoral_uuid=self.doctorate_uuid,
        )

        self.assertEqual(credits_number, 10)

        # Only keep the accepted activities
        for status in StatutActivite.get_names_except(StatutActivite.ACCEPTEE.name):
            conference.status = status
            conference.save()

            credits_number = Activity.objects.get_doctoral_training_credits_number(
                parcours_doctoral_uuid=self.doctorate_uuid,
            )

            self.assertEqual(credits_number, 0)

        # Only keep the activities from the doctoral training context
        conference.status = StatutActivite.ACCEPTEE.name
        for context in ContexteFormation.get_names_except(ContexteFormation.DOCTORAL_TRAINING.name):
            conference.context = context
            conference.save()

            credits_number = Activity.objects.get_doctoral_training_credits_number(
                parcours_doctoral_uuid=self.doctorate_uuid,
            )

            self.assertEqual(credits_number, 0)

        # Only keep the completed ucl course
        ucl_course = UclCourseFactory(
            context=ContexteFormation.DOCTORAL_TRAINING.name,
            parcours_doctoral=self.doctorate,
            status=StatutActivite.ACCEPTEE.name,
            ects=13,
            course_completed=True,
        )

        credits_number = Activity.objects.get_doctoral_training_credits_number(
            parcours_doctoral_uuid=self.doctorate_uuid,
        )

        self.assertEqual(credits_number, 13)

        ucl_course.course_completed = False
        ucl_course.save()

        credits_number = Activity.objects.get_doctoral_training_credits_number(
            parcours_doctoral_uuid=self.doctorate_uuid,
        )

        self.assertEqual(credits_number, 0)

    def test_has_complementary_training(self):
        has_complementary_training = Activity.objects.has_complementary_training(
            parcours_doctoral_uuid=self.doctorate_uuid,
        )

        self.assertFalse(has_complementary_training)

        conference = ActivityFactory(
            parcours_doctoral=self.doctorate,
            context=ContexteFormation.COMPLEMENTARY_TRAINING.name,
            category=CategorieActivite.CONFERENCE.name,
            status=StatutActivite.ACCEPTEE.name,
            ects=10,
        )

        has_complementary_training = Activity.objects.has_complementary_training(
            parcours_doctoral_uuid=self.doctorate_uuid,
        )

        self.assertTrue(has_complementary_training)

        # Only keep the accepted activities
        for status in StatutActivite.get_names_except(StatutActivite.ACCEPTEE.name):
            conference.status = status
            conference.save()

            has_complementary_training = Activity.objects.has_complementary_training(
                parcours_doctoral_uuid=self.doctorate_uuid,
            )

            self.assertFalse(has_complementary_training)

        # Only keep the activities from the complementary training context
        conference.status = StatutActivite.ACCEPTEE.name
        for context in ContexteFormation.get_names_except(ContexteFormation.COMPLEMENTARY_TRAINING.name):
            conference.context = context
            conference.save()

            has_complementary_training = Activity.objects.has_complementary_training(
                parcours_doctoral_uuid=self.doctorate_uuid,
            )

            self.assertFalse(has_complementary_training)

        # Only keep the completed ucl course
        ucl_course = UclCourseFactory(
            context=ContexteFormation.COMPLEMENTARY_TRAINING.name,
            parcours_doctoral=self.doctorate,
            status=StatutActivite.ACCEPTEE.name,
            ects=13,
            course_completed=True,
        )

        has_complementary_training = Activity.objects.has_complementary_training(
            parcours_doctoral_uuid=self.doctorate_uuid,
        )

        self.assertTrue(has_complementary_training)

        ucl_course.course_completed = False
        ucl_course.save()

        has_complementary_training = Activity.objects.has_complementary_training(
            parcours_doctoral_uuid=self.doctorate_uuid,
        )

        self.assertFalse(has_complementary_training)
