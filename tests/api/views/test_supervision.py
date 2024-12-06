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
from base.tests import QueriesAssertionsMixin
from base.tests.factories.person import PersonFactory
from django.shortcuts import resolve_url
from rest_framework import status
from rest_framework.test import APITestCase

from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.roles import StudentRoleFactory
from parcours_doctoral.tests.factories.supervision import (
    CaMemberFactory,
    PromoterFactory,
)


@freezegun.freeze_time('2023-01-01')
class SupervisionAPIViewTestCase(QueriesAssertionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Users
        cls.student = StudentRoleFactory().person
        cls.other_student = StudentRoleFactory().person
        cls.no_role_user = PersonFactory().user
        promoter = PromoterFactory(actor_ptr__person__first_name="Joe")
        cls.process = promoter.process
        cls.promoter_user = promoter.person.user
        cls.other_promoter_user = PromoterFactory().person.user
        cls.committee_member_user = CaMemberFactory(process=cls.process).person.user
        cls.other_committee_member_user = CaMemberFactory().person.user
        cls.doctorate = ParcoursDoctoralFactory(
            supervision_group=cls.process,
            student=cls.student,
        )
        cls.base_url = 'parcours_doctoral_api_v1:supervision'
        cls.url = resolve_url(cls.base_url, uuid=cls.doctorate.uuid)

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

    def test_get_supervision_with_user_not_logged_is_forbidden(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_supervision_with_user_with_no_role_is_forbidden(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_project_of_in_creation_doctorate_is_forbidden(self):
        in_creation_doctorate = ParcoursDoctoralFactory(
            supervision_group=self.doctorate.supervision_group,
            student=self.student,
            status=ChoixStatutParcoursDoctoral.EN_COURS_DE_CREATION_PAR_GESTIONNAIRE.name,
        )

        url = resolve_url(self.base_url, uuid=in_creation_doctorate.uuid)

        users = [
            self.promoter_user,
            self.committee_member_user,
            self.student.user,
        ]

        for user in users:
            self.client.force_authenticate(user=user)
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        in_creation_doctorate.status = ChoixStatutParcoursDoctoral.EN_ATTENTE_INJECTION_EPC.name
        in_creation_doctorate.save()

        for user in users:
            self.client.force_authenticate(user=user)
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_supervision_with_student(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        with self.assertNumQueriesLessThan(8):
            response = self.client.get(self.url)
        promoteurs = response.json()['signatures_promoteurs']
        self.assertEqual(len(promoteurs), 1)
        self.assertEqual(promoteurs[0]['statut'], 'NOT_INVITED')
        self.assertEqual(promoteurs[0]['promoteur']['prenom'], 'Joe')

        self.client.force_authenticate(user=self.other_student.user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_supervision_with_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_supervision_with_ca_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.other_committee_member_user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
