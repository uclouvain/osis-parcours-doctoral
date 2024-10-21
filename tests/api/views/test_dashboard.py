# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from base.tests.factories.person import PersonFactory
from django.shortcuts import resolve_url
from rest_framework import status
from rest_framework.test import APITestCase

from parcours_doctoral.tests.factories.roles import StudentRoleFactory
from parcours_doctoral.tests.factories.supervision import (
    CaMemberFactory,
    PromoterFactory,
)
from parcours_doctoral.tests.mixins import CheckActionLinksMixin


@freezegun.freeze_time('2023-01-01')
class DashboardApiViewTestCase(CheckActionLinksMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Users
        cls.student = StudentRoleFactory().person
        cls.no_role_user = PersonFactory().user
        cls.promoter_user = PromoterFactory().person.user
        cls.committee_member_user = CaMemberFactory().person.user
        cls.url = resolve_url('parcours_doctoral_api_v1:dashboard')

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

    def test_get_dashboard_with_user_not_logged_is_forbidden(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_dashboard_with_user_with_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()
        self.assertIn('links', json_response)

        self.assertActionLinks(
            links=json_response['links'],
            allowed_actions=[],
            forbidden_actions=['list', 'supervised_list'],
        )

    def test_get_dashboard_with_student(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()
        self.assertIn('links', json_response)

        self.assertActionLinks(
            links=json_response['links'],
            allowed_actions=['list'],
            forbidden_actions=['supervised_list'],
        )

    def test_get_dashboard_with_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()
        self.assertIn('links', json_response)

        self.assertActionLinks(
            links=json_response['links'],
            allowed_actions=['supervised_list'],
            forbidden_actions=['list'],
        )

    def test_get_dashboard_with_ca_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()
        self.assertIn('links', json_response)

        self.assertActionLinks(
            links=json_response['links'],
            allowed_actions=['supervised_list'],
            forbidden_actions=['list'],
        )
