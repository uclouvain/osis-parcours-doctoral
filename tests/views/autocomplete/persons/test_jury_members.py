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

from django.contrib.auth.models import AnonymousUser, User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from parcours_doctoral.ddd.jury.domain.model.enums import RoleJury
from parcours_doctoral.models import JuryActor
from parcours_doctoral.tests.factories.jury import (
    ExternalJuryMemberFactory,
    JuryMemberFactory,
    JuryMemberWithExternalPromoterFactory,
    JuryMemberWithInternalPromoterFactory,
)
from parcours_doctoral.views.autocomplete.persons import JuryMembersAutocomplete


class JuryMembersAutocompleteTestCase(TestCase):
    @classmethod
    def _formatted_person_result(cls, jury_member: JuryActor):
        if jury_member.person:
            complete_name = '{}, {}'.format(jury_member.person.last_name, jury_member.person.first_name)
        else:
            complete_name = '{}, {}'.format(jury_member.last_name, jury_member.first_name)
        return {
            'id': str(jury_member.uuid),
            'text': complete_name,
        }

    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()
        cls.user = User.objects.create_user(
            username='jacob',
            password='top_secret',
        )
        cls.jury_member = JuryMemberFactory(
            person__first_name='John',
            person__last_name='Poe',
        )
        cls.external_jury_member = ExternalJuryMemberFactory(
            first_name='Jim',
            last_name='Poe',
        )
        cls.jury_member_with_internal_promoter = JuryMemberWithInternalPromoterFactory(
            person__first_name='Jane',
            person__last_name='Doe',
        )
        cls.jury_member_with_external_promoter = JuryMemberWithExternalPromoterFactory(
            first_name='Tom',
            last_name='Doe',
        )

        cls.url = reverse('parcours_doctoral:autocomplete:jury-members')

    def test_redirects_with_anonymous_user(self):
        request = self.factory.get(self.url)
        request.user = AnonymousUser()

        response = JuryMembersAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 302)

    def test_without_query(self):
        request = self.factory.get(self.url)
        request.user = self.user

        response = JuryMembersAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [],
            },
        )

    def test_with_name_for_an_internal_jury_member(self):
        request = self.factory.get(self.url, data={'q': 'John Poe'})
        request.user = self.user

        response = JuryMembersAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    self._formatted_person_result(self.jury_member),
                ],
            },
        )

    def test_with_name_for_an_external_jury_member(self):
        request = self.factory.get(self.url, data={'q': 'Jim Poe'})
        request.user = self.user

        response = JuryMembersAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    self._formatted_person_result(self.external_jury_member),
                ],
            },
        )

    def test_with_name_for_an_jury_member_with_an_internal_promoter(self):
        request = self.factory.get(self.url, data={'q': 'Jane Doe'})
        request.user = self.user

        response = JuryMembersAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    self._formatted_person_result(self.jury_member_with_internal_promoter),
                ],
            },
        )

    def test_with_name_for_an_jury_member_with_an_external_promoter(self):
        request = self.factory.get(self.url, data={'q': 'Tom Doe'})
        request.user = self.user

        response = JuryMembersAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    self._formatted_person_result(self.jury_member_with_external_promoter),
                ],
            },
        )

    def test_with_global_id_for_an_internal_jury_member(self):
        request = self.factory.get(self.url, data={'q': self.jury_member.person.global_id})
        request.user = self.user

        response = JuryMembersAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    self._formatted_person_result(self.jury_member),
                ],
            },
        )

    def test_with_global_id_for_an_jury_member_with_an_internal_promoter(self):
        request = self.factory.get(
            self.url,
            data={
                'q': self.jury_member_with_internal_promoter.person.global_id,
            },
        )
        request.user = self.user

        response = JuryMembersAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    self._formatted_person_result(self.jury_member_with_internal_promoter),
                ],
            },
        )

    def test_filter_by_role(self):
        request = self.factory.get(
            self.url,
            data={
                'q': self.jury_member.person.global_id,
                'forward': json.dumps({'role': RoleJury.PRESIDENT.name}),
            },
        )
        request.user = self.user

        response = JuryMembersAutocomplete.as_view()(request)
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
                'q': self.jury_member.person.global_id,
                'forward': json.dumps({'role': RoleJury.MEMBRE.name}),
            },
        )
        request.user = self.user

        response = JuryMembersAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    self._formatted_person_result(self.jury_member),
                ],
            },
        )
