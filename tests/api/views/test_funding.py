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
import datetime
from unittest import mock
from uuid import uuid4

import freezegun
from django.shortcuts import resolve_url
from rest_framework import status
from rest_framework.test import APITestCase

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixTypeContratTravail,
)
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory
from parcours_doctoral.ddd.domain.model.enums import ChoixTypeFinancement
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.roles import StudentRoleFactory
from parcours_doctoral.tests.factories.supervision import (
    CaMemberFactory,
    PromoterFactory,
)
from reference.tests.factories.scholarship import DoctorateScholarshipFactory


@freezegun.freeze_time('2023-01-01')
class FundingApiViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.institution = OrganizationFactory()
        cls.file_uuids = {
            'scholarship_proof': uuid4(),
        }
        cls.scholarship = DoctorateScholarshipFactory()

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
        self.url = resolve_url('parcours_doctoral_api_v1:funding', uuid=self.doctorate.uuid)

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

    def test_get_funding_with_user_not_logged_is_forbidden(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_funding_with_user_with_no_role_is_forbidden(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_funding_with_student(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.other_student.user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_funding_with_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_funding_with_ca_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.other_committee_member_user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_funding_with_student(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.put(
            self.url,
            {
                'type': ChoixTypeFinancement.WORK_CONTRACT.name,
                'type_contrat_travail': ChoixTypeContratTravail.UCLOUVAIN_SCIENTIFIC_STAFF.name,
                'eft': 10,
                'bourse_recherche': self.scholarship.uuid,
                'autre_bourse_recherche': 'Other scholarship',
                'bourse_date_debut': datetime.date(2020, 1, 1).isoformat(),
                'bourse_date_fin': datetime.date(2022, 1, 1).isoformat(),
                'bourse_preuve': [str(self.file_uuids['scholarship_proof'])],
                'duree_prevue': 20,
                'temps_consacre': 30,
                'est_lie_fnrs_fria_fresh_csc': True,
                'commentaire': 'Comment',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.other_student.user)

        self.doctorate.refresh_from_db()

        self.assertEqual(self.doctorate.financing_type, ChoixTypeFinancement.WORK_CONTRACT.name)
        self.assertEqual(
            self.doctorate.financing_work_contract,
            ChoixTypeContratTravail.UCLOUVAIN_SCIENTIFIC_STAFF.name,
        )
        self.assertEqual(self.doctorate.financing_eft, 10)
        self.assertEqual(self.doctorate.international_scholarship, self.scholarship)
        self.assertEqual(self.doctorate.other_international_scholarship, 'Other scholarship')
        self.assertEqual(self.doctorate.scholarship_start_date, datetime.date(2020, 1, 1))
        self.assertEqual(self.doctorate.scholarship_end_date, datetime.date(2022, 1, 1))
        self.assertEqual(self.doctorate.scholarship_proof, [self.file_uuids['scholarship_proof']])
        self.assertEqual(self.doctorate.planned_duration, 20)
        self.assertEqual(self.doctorate.dedicated_time, 30)
        self.assertEqual(self.doctorate.is_fnrs_fria_fresh_csc_linked, True)
        self.assertEqual(self.doctorate.financing_comment, 'Comment')
