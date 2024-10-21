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
from unittest import mock
from uuid import uuid4

import freezegun
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory
from django.shortcuts import resolve_url
from rest_framework import status
from rest_framework.test import APITestCase

from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.roles import StudentRoleFactory
from parcours_doctoral.tests.factories.supervision import (
    CaMemberFactory,
    PromoterFactory,
)


@freezegun.freeze_time('2023-01-01')
class CotutelleAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.institution = OrganizationFactory()
        cls.file_uuids = {
            'cotutelle_opening_request': uuid4(),
            'cotutelle_convention': uuid4(),
            'cotutelle_other_documents': uuid4(),
        }

        # Users
        cls.student = StudentRoleFactory().person
        cls.other_student = StudentRoleFactory().person
        cls.no_role_user = PersonFactory().user
        promoter = PromoterFactory()
        cls.process = promoter.process
        cls.promoter_user = promoter.person.user
        cls.other_promoter_user = PromoterFactory().person.user
        cls.committee_member_user = CaMemberFactory(process=cls.process).person.user
        cls.other_committee_member_user = CaMemberFactory().person.user

    def setUp(self):
        self.doctorate = ParcoursDoctoralFactory(
            supervision_group=self.process,
            student=self.student,
        )
        self.url = resolve_url('parcours_doctoral_api_v1:cotutelle', uuid=self.doctorate.uuid)

        patcher = mock.patch(
            "osis_document.contrib.fields.FileField._confirm_multiple_upload",
            side_effect=lambda _, value, __: value,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.student.user)
        methods_not_allowed = [
            'delete',
            'patch',
            'post',
        ]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_cotutelle_with_user_not_logged_is_forbidden(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_cotutelle_with_user_with_no_role_is_forbidden(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_cotutelle_with_student(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.other_student.user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_cotutelle_with_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_cotutelle_with_ca_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.other_committee_member_user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_cotutelle_with_student(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.put(
            self.url,
            {
                'cotutelle': True,
                'motivation': 'abc',
                'institution_fwb': True,
                'institution': self.institution.uuid,
                'autre_institution_nom': 'Institution A',
                'autre_institution_adresse': 'Address A',
                'demande_ouverture': [str(self.file_uuids['cotutelle_opening_request'])],
                'convention': [str(self.file_uuids['cotutelle_convention'])],
                'autres_documents': [str(self.file_uuids['cotutelle_other_documents'])],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.other_student.user)

        self.doctorate.refresh_from_db()

        self.assertTrue(self.doctorate.cotutelle)
        self.assertEqual(self.doctorate.cotutelle_motivation, 'abc')
        self.assertTrue(self.doctorate.cotutelle_institution_fwb)
        self.assertEqual(self.doctorate.cotutelle_institution, self.institution.uuid)
        self.assertEqual(self.doctorate.cotutelle_other_institution_name, 'Institution A')
        self.assertEqual(self.doctorate.cotutelle_other_institution_address, 'Address A')
        self.assertEqual(self.doctorate.cotutelle_opening_request, [self.file_uuids['cotutelle_opening_request']])
        self.assertEqual(self.doctorate.cotutelle_convention, [self.file_uuids['cotutelle_convention']])
        self.assertEqual(self.doctorate.cotutelle_other_documents, [self.file_uuids['cotutelle_other_documents']])
