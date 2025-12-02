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
from rest_framework import status
from rest_framework.test import APITestCase

from base.tests.factories.user import UserFactory
from parcours_doctoral.models.private_defense import PrivateDefense
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.private_defense import PrivateDefenseFactory
from parcours_doctoral.tests.factories.roles import StudentRoleFactory


class PrivateDefenseListAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_with_no_role = UserFactory()
        cls.doctorate_student = StudentRoleFactory().person
        cls.other_doctorate_student = StudentRoleFactory().person

        cls.doctorate = ParcoursDoctoralFactory(
            student=cls.doctorate_student,
            thesis_proposed_title='T1',
        )
        cls.other_doctorate = ParcoursDoctoralFactory(
            student=cls.other_doctorate_student,
            thesis_proposed_title='T2',
        )

        cls.url = resolve_url('parcours_doctoral_api_v1:private-defense-list', uuid=cls.doctorate.uuid)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        methods_not_allowed = [
            'delete',
            'patch',
            'post',
        ]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_access_with_no_role(self):
        self.client.force_authenticate(self.user_with_no_role)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_access_other_student(self):
        self.client.force_authenticate(self.other_doctorate_student.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_with_no_private_defense(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()
        self.assertEqual(len(json_response), 0)

    def test_get_with_several_private_defenses(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        with freezegun.freeze_time('2020-01-01'):
            first_private_defense: PrivateDefense = PrivateDefenseFactory(
                parcours_doctoral=self.doctorate,
                current_parcours_doctoral=None,
            )

        with freezegun.freeze_time('2020-01-05'):
            second_private_defense: PrivateDefense = PrivateDefenseFactory(
                parcours_doctoral=self.doctorate,
            )

        PrivateDefenseFactory(
            parcours_doctoral=self.other_doctorate,
        )

        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        private_defenses = response.json()
        self.assertEqual(len(private_defenses), 2)

        self.assertEqual(private_defenses[0].get('uuid'), str(second_private_defense.uuid))
        self.assertTrue(private_defenses[0].get('est_active'))
        self.assertEqual(private_defenses[0].get('date_heure'), second_private_defense.datetime.isoformat())
        self.assertEqual(private_defenses[0].get('lieu'), second_private_defense.place)
        self.assertEqual(
            private_defenses[0].get('date_envoi_manuscrit'),
            second_private_defense.manuscript_submission_date.isoformat(),
        )
        self.assertEqual(private_defenses[0].get('proces_verbal')[0], str(second_private_defense.minutes[0]))
        self.assertEqual(
            private_defenses[0].get('canevas_proces_verbal')[0],
            str(second_private_defense.minutes_canvas[0]),
        )

        self.assertEqual(private_defenses[1].get('uuid'), str(first_private_defense.uuid))
        self.assertFalse(private_defenses[1].get('est_active'))
        self.assertEqual(private_defenses[1].get('date_heure'), first_private_defense.datetime.isoformat())
        self.assertEqual(private_defenses[1].get('lieu'), first_private_defense.place)
        self.assertEqual(
            private_defenses[1].get('date_envoi_manuscrit'),
            first_private_defense.manuscript_submission_date.isoformat(),
        )
        self.assertEqual(private_defenses[1].get('proces_verbal')[0], str(first_private_defense.minutes[0]))
        self.assertEqual(
            private_defenses[1].get('canevas_proces_verbal')[0],
            str(first_private_defense.minutes_canvas[0]),
        )
