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
import datetime
from unittest import mock
from uuid import uuid4

import freezegun
from django.shortcuts import resolve_url
from rest_framework import status
from rest_framework.test import APITestCase

from base.tests.factories.person import PersonFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.epreuve_confirmation.validators.exceptions import (
    EpreuveConfirmationNonTrouveeException,
)
from parcours_doctoral.models import ConfirmationPaper
from parcours_doctoral.tests.factories.confirmation_paper import (
    ConfirmationPaperFactory,
)
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.roles import StudentRoleFactory
from parcours_doctoral.tests.factories.supervision import (
    CaMemberFactory,
    PromoterFactory,
)


@freezegun.freeze_time('2023-01-01')
class SupervisedConfirmationAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.file_uuids = {
            'supervisor_panel_report': uuid4(),
            'research_mandate_renewal_opinion': uuid4(),
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

        cls.doctorate = ParcoursDoctoralFactory(
            supervision_group=cls.process,
            student=cls.student,
            status=ChoixStatutParcoursDoctoral.ADMIS.name,
        )

        cls.manager = ProgramManagerFactory(education_group=cls.doctorate.training.education_group).person

        cls.base_url = 'parcours_doctoral_api_v1:supervised_confirmation'

        cls.url = resolve_url(cls.base_url, uuid=cls.doctorate.uuid)

    def setUp(self):
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
            'get',
            'patch',
            'post',
        ]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_confirmation_with_user_not_logged_is_forbidden(self):
        self.client.force_authenticate(user=None)
        response = self.client.put(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_confirmation_with_user_with_no_role_is_forbidden(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.put(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_confirmation_with_student_is_forbidden(self):
        self.client.force_authenticate(user=self.other_student.user)
        response = self.client.put(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.student.user)
        response = self.client.put(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_last_confirmation_with_ca_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.put(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.other_committee_member_user)
        response = self.client.put(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_confirmation_of_in_creation_doctorate_is_forbidden(self):
        self.client.force_authenticate(user=self.promoter_user)

        in_creation_doctorate = ParcoursDoctoralFactory(
            supervision_group=self.doctorate.supervision_group,
            student=self.student,
            status=ChoixStatutParcoursDoctoral.EN_COURS_DE_CREATION_PAR_GESTIONNAIRE.name,
        )

        url = resolve_url(self.base_url, uuid=in_creation_doctorate.uuid)

        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        in_creation_doctorate.status = ChoixStatutParcoursDoctoral.EN_ATTENTE_INJECTION_EPC.name
        in_creation_doctorate.save()

        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_confirmation_with_promoter(self):
        self.client.force_authenticate(user=self.other_promoter_user)

        response = self.client.put(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.promoter_user)

        default_data = {
            'proces_verbal_ca': [str(self.file_uuids['supervisor_panel_report'])],
            'avis_renouvellement_mandat_recherche': [str(self.file_uuids['research_mandate_renewal_opinion'])],
        }

        # No confirmation paper
        response = self.client.put(self.url, data=default_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            EpreuveConfirmationNonTrouveeException.status_code,
        )

        # One confirmation paper
        confirmation_paper: ConfirmationPaper = ConfirmationPaperFactory(
            parcours_doctoral=self.doctorate,
            confirmation_date=datetime.date(2022, 4, 1),
        )

        response = self.client.put(self.url, data=default_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        confirmation_paper.refresh_from_db()
        self.assertEqual(confirmation_paper.supervisor_panel_report, [self.file_uuids['supervisor_panel_report']])
        self.assertEqual(
            confirmation_paper.research_mandate_renewal_opinion,
            [self.file_uuids['research_mandate_renewal_opinion']],
        )

        # Two confirmation papers
        old_confirmation_paper = ConfirmationPaperFactory(
            parcours_doctoral=self.doctorate,
            confirmation_date=datetime.date(2020, 4, 2),
        )

        response = self.client.put(self.url, data=default_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        old_confirmation_paper.refresh_from_db()

        self.assertEqual(old_confirmation_paper.supervisor_panel_report, [])
        self.assertEqual(old_confirmation_paper.research_mandate_renewal_opinion, [])
