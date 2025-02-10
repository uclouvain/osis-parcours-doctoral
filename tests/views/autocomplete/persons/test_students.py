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
from django.contrib.auth.models import AnonymousUser, User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from base.models.person import Person
from base.models.student import Student
from base.tests.factories.person import PersonFactory
from base.tests.factories.student import StudentFactory
from parcours_doctoral.tests.factories.roles import StudentRoleFactory
from parcours_doctoral.views.autocomplete.persons import StudentsAutocomplete


class StudentsAutocompleteTestCase(TestCase):
    @classmethod
    def _formatted_person_result(cls, p: Person):
        return {
            'id': p.global_id,
            'text': '{}, {}'.format(p.last_name, p.first_name),
        }

    @classmethod
    def setUpTestData(cls):
        cls.factory = RequestFactory()
        cls.user = User.objects.create_user(
            username='jacob',
            password='top_secret',
        )
        cls.first_student = StudentRoleFactory(
            person=StudentFactory(
                person=PersonFactory(
                    first_name='John',
                    last_name='Poe',
                )
            ).person,
        ).person
        cls.second_student = StudentRoleFactory(
            person=StudentFactory(
                person=PersonFactory(
                    first_name='Jane',
                    last_name='Poe',
                )
            ).person,
        ).person

        cls.url = reverse('parcours_doctoral:autocomplete:students')

    def test_redirects_with_anonymous_user(self):
        request = self.factory.get(self.url)
        request.user = AnonymousUser()

        response = StudentsAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 302)

    def test_without_query(self):
        request = self.factory.get(self.url)
        request.user = self.user

        response = StudentsAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [],
            },
        )

    def test_with_name(self):
        request = self.factory.get(self.url, data={'q': 'Poe'})
        request.user = self.user

        response = StudentsAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    self._formatted_person_result(self.second_student),
                    self._formatted_person_result(self.first_student),
                ],
            },
        )

    def test_with_global_id(self):
        request = self.factory.get(self.url, data={'q': self.first_student.global_id})
        request.user = self.user

        response = StudentsAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    self._formatted_person_result(self.first_student),
                ],
            },
        )

    def test_with_noma(self):
        second_student = Student.objects.filter(person=self.second_student).first()
        request = self.factory.get(self.url, data={'q': second_student.registration_id})
        request.user = self.user

        response = StudentsAutocomplete.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'pagination': {'more': False},
                'results': [
                    self._formatted_person_result(self.second_student),
                ],
            },
        )
