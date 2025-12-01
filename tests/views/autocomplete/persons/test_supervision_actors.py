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
import json

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from parcours_doctoral.models import ActorType, ParcoursDoctoralSupervisionActor
from parcours_doctoral.tests.factories.supervision import (
    CaMemberFactory,
    ExternalPromoterFactory,
    PromoterFactory,
)
from parcours_doctoral.views.autocomplete.persons import SupervisionActorsAutocomplete


class SupervisionActorsAutocompleteTestCase(TestCase):
    @classmethod
    def _formatted_person_result(cls, supervision_actor: ParcoursDoctoralSupervisionActor):
        return {
            'id': str(supervision_actor.uuid),
            'text': '{}, {}'.format(supervision_actor.last_name, supervision_actor.first_name),
        }

    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()
        cls.user = User.objects.create_user(
            username='jacob',
            password='top_secret',
        )
        cls.ca_member = CaMemberFactory(
            actor_ptr__person__first_name='John',
            actor_ptr__person__last_name='Poe',
        )
        cls.promoter = PromoterFactory(
            actor_ptr__person__first_name='Jane',
            actor_ptr__person__last_name='Poe',
        )
        cls.external_promoter = ExternalPromoterFactory(
            first_name='John',
            last_name='Doe',
        )

        cls.url = reverse('parcours_doctoral:autocomplete:supervision-actors')

    def test_redirects_with_anonymous_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_without_query(self):
        request = self.factory.get(self.url)
        request.user = self.user

        response = SupervisionActorsAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [],
            },
        )

    def test_with_name_for_an_internal_actor(self):
        request = self.factory.get(self.url, data={'q': 'Poe'})
        request.user = self.user

        response = SupervisionActorsAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    self._formatted_person_result(self.promoter),
                    self._formatted_person_result(self.ca_member),
                ],
            },
        )

    def test_with_name_for_an_external_actor(self):
        request = self.factory.get(self.url, data={'q': 'Doe'})
        request.user = self.user

        response = SupervisionActorsAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    self._formatted_person_result(self.external_promoter),
                ],
            },
        )

    def test_with_global_id(self):
        request = self.factory.get(self.url, data={'q': self.promoter.person.global_id})
        request.user = self.user

        response = SupervisionActorsAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    self._formatted_person_result(self.promoter),
                ],
            },
        )

    def test_with_actor_type(self):
        request = self.factory.get(
            self.url,
            data={
                'q': self.promoter.person.global_id,
                'forward': json.dumps(
                    {
                        'actor_type': ActorType.CA_MEMBER.name,
                    }
                ),
            },
        )
        request.user = self.user

        response = SupervisionActorsAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [],
            },
        )

        request = self.factory.get(
            self.url,
            data={
                'q': self.promoter.person.global_id,
                'forward': json.dumps(
                    {
                        'actor_type': ActorType.PROMOTER.name,
                    }
                ),
            },
        )
        request.user = self.user

        response = SupervisionActorsAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    self._formatted_person_result(self.promoter),
                ],
            },
        )
