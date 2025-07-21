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
import uuid

from django.shortcuts import resolve_url
from django.utils.translation import gettext
from osis_history.models import HistoryEntry
from rest_framework import status
from rest_framework.test import APITestCase

from admission.models.mixins import DocumentCopyModelMixin
from base.tests.factories.user import UserFactory
from parcours_doctoral.ddd.defense_privee.validators.exceptions import (
    DefensePriveeNonActiveeException,
    DefensePriveeNonTrouveeException,
)
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.models import ParcoursDoctoral
from parcours_doctoral.models.private_defense import PrivateDefense
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.private_defense import PrivateDefenseFactory
from parcours_doctoral.tests.factories.roles import StudentRoleFactory


class PrivateDefenseAPIViewTestCase(DocumentCopyModelMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_with_no_role = UserFactory()
        cls.doctorate_student = StudentRoleFactory().person
        cls.other_doctorate_student = StudentRoleFactory().person

        cls.doctorate: ParcoursDoctoral = ParcoursDoctoralFactory(
            student=cls.doctorate_student,
            thesis_proposed_title='T1',
        )
        cls.other_doctorate = ParcoursDoctoralFactory(
            student=cls.other_doctorate_student,
            thesis_proposed_title='T2',
        )

        cls.data = {
            'titre_these': 'New thesis title',
            'date_heure': '2025-09-09T10:00:00',
            'lieu': 'Thesis location',
            'date_envoi_manuscrit': '2025-08-08',
        }

        cls.base_namespace = 'parcours_doctoral_api_v1:private-defense'

    def setUp(self):
        self.private_defense: PrivateDefense = PrivateDefenseFactory(parcours_doctoral=self.doctorate)

        self.doctorate.status = ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE.name
        self.doctorate.save()

        self.url = resolve_url(
            self.base_namespace,
            uuid=self.doctorate.uuid,
            private_defense_uuid=self.private_defense.uuid,
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

    def test_get_with_unknown_private_defense(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        response = self.client.get(
            resolve_url(
                self.base_namespace,
                uuid=self.doctorate.uuid,
                private_defense_uuid=uuid.uuid4(),
            ),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        json_response = response.json()
        self.assertIn(
            {
                'status_code': DefensePriveeNonTrouveeException.status_code,
                'detail': gettext('Private defense not found.'),
            },
            json_response.get('non_field_errors', []),
        )

    def test_get_a_known_private_defenses(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        private_defense = response.json()

        self.assertEqual(private_defense.get('uuid'), str(self.private_defense.uuid))
        self.assertTrue(private_defense.get('est_active'))
        self.assertEqual(private_defense.get('titre_these'), self.doctorate.thesis_proposed_title)
        self.assertEqual(private_defense.get('date_heure'), self.private_defense.datetime.isoformat())
        self.assertEqual(private_defense.get('lieu'), self.private_defense.place)
        self.assertEqual(
            private_defense.get('date_envoi_manuscrit'),
            self.private_defense.manuscript_submission_date.isoformat(),
        )
        self.assertEqual(private_defense.get('proces_verbal')[0], str(self.private_defense.minutes[0]))
        self.assertEqual(private_defense.get('canevas_proces_verbal')[0], str(self.private_defense.minutes_canvas[0]))

    def test_edit_a_known_private_defense_with_invalid_status(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        self.doctorate.status = ChoixStatutParcoursDoctoral.ADMIS.name
        self.doctorate.save()

        # Invalid status
        response = self.client.put(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        json_response = response.json()
        self.assertEqual(json_response.get('detail'), gettext('The private defense is not in progress'))

    def test_edit_a_known_private_defense_with_valid_data(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        # First submission with valid data
        response = self.client.put(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.private_defense.refresh_from_db()
        self.doctorate.refresh_from_db()

        self.assertEqual(self.doctorate.status, ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE.name)
        self.assertEqual(self.doctorate.thesis_proposed_title, 'New thesis title')
        self.assertEqual(self.private_defense.datetime, datetime.datetime(2025, 9, 9, 10))
        self.assertEqual(self.private_defense.place, 'Thesis location')
        self.assertEqual(self.private_defense.manuscript_submission_date, datetime.date(2025, 8, 8))

        historic_entries = HistoryEntry.objects.filter(object_uuid=self.doctorate.uuid)
        self.assertEqual(len(historic_entries), 1)
        self.assertCountEqual(historic_entries[0].tags, ["parcours_doctoral", "private-defense", "status-changed"])

        # Newer submission
        response = self.client.put(
            self.url,
            data={
                'titre_these': 'Another thesis title',
                'date_heure': '2026-09-09T11:00:00',
                'lieu': 'New thesis location',
                'date_envoi_manuscrit': '2026-08-08',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.private_defense.refresh_from_db()
        self.doctorate.refresh_from_db()

        self.assertEqual(self.doctorate.status, ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE.name)
        self.assertEqual(self.doctorate.thesis_proposed_title, 'Another thesis title')
        self.assertEqual(self.private_defense.datetime, datetime.datetime(2026, 9, 9, 11))
        self.assertEqual(self.private_defense.place, 'New thesis location')
        self.assertEqual(self.private_defense.manuscript_submission_date, datetime.date(2026, 8, 8))

        historic_entries = HistoryEntry.objects.filter(object_uuid=self.doctorate.uuid)
        self.assertEqual(len(historic_entries), 2)
        self.assertCountEqual(historic_entries[0].tags, ["parcours_doctoral", "private-defense"])

    def test_edit_a_known_private_defense_with_invalid_data(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        # Invalid data
        response = self.client.put(
            self.url,
            data={
                'titre_these': '',
                'date_heure': '',
                'lieu': '',
                'date_envoi_manuscrit': '',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_edit_a_known_but_old_private_defense(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        self.private_defense.current_parcours_doctoral = None
        self.private_defense.save()

        # Update of an old private defense
        response = self.client.put(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        json_response = response.json()
        self.assertIn(
            {
                'status_code': DefensePriveeNonActiveeException.status_code,
                'detail': gettext('Private defense not activated.'),
            },
            json_response.get('non_field_errors', []),
        )
