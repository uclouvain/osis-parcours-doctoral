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

import freezegun
from django.shortcuts import resolve_url
from osis_history.models import HistoryEntry
from rest_framework import status
from rest_framework.test import APITestCase

from base.tests.factories.user import UserFactory
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.jury.domain.model.enums import FormuleDefense
from parcours_doctoral.models import ParcoursDoctoral
from parcours_doctoral.models.admissibility import Admissibility
from parcours_doctoral.tests.factories.admissibility import AdmissibilityFactory
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.roles import StudentRoleFactory
from parcours_doctoral.tests.mixins import MockOsisDocumentMixin


class AdmissibilityListAPIViewGetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_with_no_role = UserFactory()
        cls.doctorate_student = StudentRoleFactory().person
        cls.other_doctorate_student = StudentRoleFactory().person

        cls.doctorate = ParcoursDoctoralFactory(
            student=cls.doctorate_student,
            thesis_proposed_title='T1',
            defense_method=FormuleDefense.FORMULE_2.name,
        )
        cls.other_doctorate = ParcoursDoctoralFactory(
            student=cls.other_doctorate_student,
            thesis_proposed_title='T2',
            defense_method=FormuleDefense.FORMULE_2.name,
        )

        cls.url = resolve_url('parcours_doctoral_api_v1:admissibility-list', uuid=cls.doctorate.uuid)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        methods_not_allowed = [
            'delete',
            'patch',
            'post',
        ]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_access_with_no_role(self):
        self.client.force_authenticate(self.user_with_no_role)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_access_other_student(self):
        self.client.force_authenticate(self.other_doctorate_student.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_with_no_admissibility(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()
        self.assertEqual(len(json_response), 0)

    def test_get_with_several_admissibility(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        with freezegun.freeze_time('2020-01-01'):
            first_admissibility: Admissibility = AdmissibilityFactory(
                parcours_doctoral=self.doctorate,
                current_parcours_doctoral=None,
            )

        with freezegun.freeze_time('2020-01-05'):
            second_admissibility: Admissibility = AdmissibilityFactory(
                parcours_doctoral=self.doctorate,
            )

        other_admissibility: Admissibility = AdmissibilityFactory(
            parcours_doctoral=self.other_doctorate,
        )

        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        admissibilities = response.json()
        self.assertEqual(len(admissibilities), 2)

        self.assertEqual(admissibilities[0].get('uuid'), str(second_admissibility.uuid))
        self.assertTrue(admissibilities[0].get('est_active'))
        self.assertEqual(admissibilities[0].get('date_decision'), second_admissibility.decision_date.isoformat())
        self.assertEqual(
            admissibilities[0].get('date_envoi_manuscrit'),
            second_admissibility.manuscript_submission_date.isoformat(),
        )
        self.assertEqual(admissibilities[0].get('avis_jury')[0], str(second_admissibility.thesis_exam_board_opinion[0]))
        self.assertEqual(admissibilities[0].get('proces_verbal')[0], str(second_admissibility.minutes[0]))
        self.assertEqual(
            admissibilities[0].get('canevas_proces_verbal')[0],
            str(second_admissibility.minutes_canvas[0]),
        )

        self.assertEqual(admissibilities[1].get('uuid'), str(first_admissibility.uuid))
        self.assertFalse(admissibilities[1].get('est_active'))
        self.assertEqual(admissibilities[0].get('date_decision'), second_admissibility.decision_date.isoformat())
        self.assertEqual(
            admissibilities[1].get('date_envoi_manuscrit'),
            first_admissibility.manuscript_submission_date.isoformat(),
        )
        self.assertEqual(admissibilities[1].get('avis_jury')[0], str(first_admissibility.thesis_exam_board_opinion[0]))
        self.assertEqual(admissibilities[1].get('proces_verbal')[0], str(first_admissibility.minutes[0]))
        self.assertEqual(
            admissibilities[1].get('canevas_proces_verbal')[0],
            str(first_admissibility.minutes_canvas[0]),
        )


class AdmissibilityListAPIViewPutTestCase(MockOsisDocumentMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_with_no_role = UserFactory()
        cls.doctorate_student = StudentRoleFactory().person
        cls.other_doctorate_student = StudentRoleFactory().person

        cls.other_doctorate = ParcoursDoctoralFactory(
            student=cls.other_doctorate_student,
            thesis_proposed_title='T2',
        )

        cls.data = {
            'titre_these': 'New thesis title',
            'date_decision': '2025-09-09',
            'date_envoi_manuscrit': '2025-08-08',
        }

    def setUp(self):
        self.doctorate: ParcoursDoctoral = ParcoursDoctoralFactory(
            student=self.doctorate_student,
            thesis_proposed_title='T1',
            status=ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE.name,
            defense_method=FormuleDefense.FORMULE_2.name,
        )

        self.url = resolve_url(
            to='parcours_doctoral_api_v1:admissibility-list',
            uuid=self.doctorate.uuid,
        )

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        methods_not_allowed = [
            'delete',
            'patch',
            'post',
        ]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_access_with_no_role(self):
        self.client.force_authenticate(self.user_with_no_role)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_access_other_student(self):
        self.client.force_authenticate(self.other_doctorate_student.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_edit_with_valid_data(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        # First submission with valid data
        response = self.client.put(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        admissibility = Admissibility.objects.get(parcours_doctoral=self.doctorate)

        self.doctorate.refresh_from_db()

        self.assertEqual(self.doctorate.status, ChoixStatutParcoursDoctoral.RECEVABILITE_SOUMISE.name)
        self.assertEqual(self.doctorate.thesis_proposed_title, 'New thesis title')
        self.assertEqual(admissibility.decision_date, datetime.date(2025, 9, 9))
        self.assertEqual(admissibility.manuscript_submission_date, datetime.date(2025, 8, 8))

        historic_entries = HistoryEntry.objects.filter(object_uuid=self.doctorate.uuid)
        self.assertEqual(len(historic_entries), 1)
        self.assertCountEqual(historic_entries[0].tags, ['parcours_doctoral', 'admissibility', 'status-changed'])

        # Newer submission
        response = self.client.put(
            self.url,
            data={
                'titre_these': 'Another thesis title',
                'date_decision': '2026-09-09',
                'date_envoi_manuscrit': '2026-08-08',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_admissibility = Admissibility.objects.get(parcours_doctoral=self.doctorate)
        admissibility.refresh_from_db()
        self.doctorate.refresh_from_db()

        self.assertEqual(self.doctorate.status, ChoixStatutParcoursDoctoral.RECEVABILITE_SOUMISE.name)
        self.assertEqual(self.doctorate.thesis_proposed_title, 'Another thesis title')
        self.assertEqual(updated_admissibility, admissibility)
        self.assertEqual(admissibility.decision_date, datetime.date(2026, 9, 9))
        self.assertEqual(admissibility.manuscript_submission_date, datetime.date(2026, 8, 8))

        historic_entries = HistoryEntry.objects.filter(object_uuid=self.doctorate.uuid)
        self.assertEqual(len(historic_entries), 1)

    def test_edit_a_known_private_defense_with_invalid_data(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        # Invalid data
        response = self.client.put(
            self.url,
            data={
                'titre_these': '',
                'date_decision': '',
                'date_envoi_manuscrit': '',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
