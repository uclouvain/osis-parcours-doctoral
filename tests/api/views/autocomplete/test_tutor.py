# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.shortcuts import resolve_url
from rest_framework.test import APITestCase

from admission.tests.factories.person import InternalPersonFactory
from base.models.person import Person
from base.tests.factories.person import ExternalPersonFactory
from base.tests.factories.tutor import TutorFactory
from base.tests.factories.user import UserFactory


class AutocompleteTutorViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.base_url = resolve_url('parcours_doctoral_api_v1:tutor')

    def test_autocomplete_persons_with_search_on_global_id(self):
        self.client.force_authenticate(user=self.user)
        TutorFactory(person=InternalPersonFactory(global_id='00005789'))
        response = self.client.get(
            self.base_url + '?search=57',
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['count'], 1)

    def test_autocomplete_persons_with_search_on_first_name(self):
        self.client.force_authenticate(user=self.user)
        TutorFactory(person=InternalPersonFactory(first_name='Jean-Marc'))
        response = self.client.get(
            self.base_url + '?search=jean',
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['count'], 1)

    def test_autocomplete_persons_with_search_on_last_name(self):
        self.client.force_authenticate(user=self.user)
        TutorFactory(person=InternalPersonFactory(last_name='Doe'))
        response = self.client.get(
            self.base_url + '?search=doe',
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['count'], 1)

    def test_autocomplete_persons_without_persons_with_empty_global_id(self):
        self.client.force_authenticate(user=self.user)
        TutorFactory(person__global_id=None, person__first_name='John', person__last_name='Doe')
        response = self.client.get(
            self.base_url + '?search=doe',
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['count'], 0)

    def test_autocomplete_persons_without_persons_with_external_account(self):
        self.client.force_authenticate(user=self.user)
        TutorFactory(person=ExternalPersonFactory())
        response = self.client.get(
            self.base_url + '?search=57',
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['count'], 0)
