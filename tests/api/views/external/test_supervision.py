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
from osis_signature.enums import SignatureState
from osis_signature.utils import get_signing_token
from rest_framework import status
from rest_framework.test import APITestCase

from base.tests import QueriesAssertionsMixin
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.roles import StudentRoleFactory
from parcours_doctoral.tests.factories.supervision import ExternalPromoterFactory


@freezegun.freeze_time('2023-01-01')
class ExternalDoctorateSupervisionAPIViewTestCase(QueriesAssertionsMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Users
        cls.student = StudentRoleFactory().person
        cls.other_student = StudentRoleFactory().person
        cls.external_promoter = ExternalPromoterFactory()
        cls.external_promoter.actor_ptr.switch_state(SignatureState.INVITED)
        cls.doctorate = ParcoursDoctoralFactory(
            supervision_group=cls.external_promoter.process,
            student=cls.student,
        )
        cls.base_url = 'parcours_doctoral_api_v1:external-supervision'

    def test_supervision_bad_token(self):
        # Invalid token
        response = self.client.get(resolve_url(self.base_url, uuid=self.doctorate.uuid, token='bad-token'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Valid token but of another supervision group
        other_external_promoter = ExternalPromoterFactory()
        other_external_promoter.actor_ptr.switch_state(SignatureState.INVITED)

        response = self.client.get(
            resolve_url(
                self.base_url,
                uuid=self.doctorate.uuid,
                token=get_signing_token(other_external_promoter),
            )
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Valid token of the same supervision group but too old
        with freezegun.freeze_time('2022-01-01'):
            other_external_promoter = ExternalPromoterFactory()
            other_external_promoter.actor_ptr.switch_state(SignatureState.INVITED)

        response = self.client.get(
            resolve_url(
                self.base_url,
                uuid=self.doctorate.uuid,
                token=get_signing_token(other_external_promoter),
            )
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supervision_get_info(self):
        token = get_signing_token(self.external_promoter)
        url = resolve_url(self.base_url, uuid=self.doctorate.uuid, token=token)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('supervision', data)
        self.assertEqual(len(data['supervision']['signatures_promoteurs']), 1)
        self.assertIn('parcours_doctoral', data)
        self.assertEqual(data['parcours_doctoral']['uuid'], str(self.doctorate.uuid))

    def test_supervision_with_in_creation_doctorate_is_forbidden(self):
        in_creation_doctorate = ParcoursDoctoralFactory(
            supervision_group=self.doctorate.supervision_group,
            student=self.student,
            create_student__with_valid_enrolment=False,
        )

        token = get_signing_token(self.external_promoter)
        url = resolve_url(self.base_url, uuid=in_creation_doctorate.uuid, token=token)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
