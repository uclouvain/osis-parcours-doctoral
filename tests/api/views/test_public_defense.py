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
from django.test import override_settings
from django.utils.translation import gettext
from osis_history.models import HistoryEntry
from rest_framework import status
from rest_framework.test import APITestCase

from base.tests.factories.user import UserFactory
from parcours_doctoral.ddd.domain.model.enums import (
    ChoixLangueDefense,
    ChoixStatutParcoursDoctoral,
)
from parcours_doctoral.ddd.soutenance_publique.validators.exceptions import (
    SoutenancePubliqueNonCompleteeException,
)
from parcours_doctoral.models import ParcoursDoctoral
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.roles import StudentRoleFactory
from parcours_doctoral.tests.mixins import MockOsisDocumentMixin
from reference.tests.factories.language import LanguageFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class PublicDefenseAPIViewTestCase(MockOsisDocumentMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user_with_no_role = UserFactory()
        cls.doctorate_student = StudentRoleFactory().person
        cls.other_doctorate_student = StudentRoleFactory().person

        cls.other_doctorate = ParcoursDoctoralFactory(
            student=cls.other_doctorate_student,
            thesis_proposed_title='T2',
        )

        cls.language = LanguageFactory()

        cls.base_namespace = 'parcours_doctoral_api_v1:public-defense'

    def setUp(self):
        super().setUp()

        self.doctorate: ParcoursDoctoral = ParcoursDoctoralFactory(
            student=self.doctorate_student,
            thesis_proposed_title='T1',
            status=ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_REUSSIE.name,
        )

        self.data = {
            'langue': self.language.code,
            'date_heure': datetime.datetime(2022, 1, 2, 11, 30),
            'lieu': 'Louvain-La-Neuve',
            'local_deliberation': 'L1',
            'resume_annonce': 'Summary of the public defense',
            'photo_annonce': [uuid.uuid4()],
        }

        self.url = resolve_url(
            self.base_namespace,
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

    def test_get_with_unknown_doctorate(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        response = self.client.get(
            resolve_url(
                self.base_namespace,
                uuid=uuid.uuid4(),
            ),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_edit_a_known_private_defense_with_invalid_status(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        self.doctorate.status = ChoixStatutParcoursDoctoral.ADMIS.name
        self.doctorate.save()

        # Invalid status
        response = self.client.put(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        json_response = response.json()
        self.assertEqual(json_response.get('detail'), gettext('The public defense is not in progress'))

    def test_edit_a_known_private_defense_with_valid_data(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        # First submission with valid data
        response = self.client.put(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.doctorate.refresh_from_db()

        self.assertEqual(self.doctorate.status, ChoixStatutParcoursDoctoral.SOUTENANCE_PUBLIQUE_SOUMISE.name)
        self.assertEqual(self.doctorate.defense_language, self.language)
        self.assertEqual(self.doctorate.defense_datetime, self.data['date_heure'])
        self.assertEqual(self.doctorate.defense_place, self.data['lieu'])
        self.assertEqual(self.doctorate.defense_deliberation_room, self.data['local_deliberation'])
        self.assertEqual(self.doctorate.announcement_summary, self.data['resume_annonce'])
        self.assertEqual(self.doctorate.announcement_photo, [uuid.UUID('4bdffb42-552d-415d-9e4c-725f10dce228')])

        historic_entries = HistoryEntry.objects.filter(object_uuid=self.doctorate.uuid)
        self.assertEqual(len(historic_entries), 1)
        self.assertCountEqual(historic_entries[0].tags, ['parcours_doctoral', 'public-defense', 'status-changed'])

        # Newer submission with minimal data
        new_data = {
            'langue': self.language.iso_code,
            'date_heure': datetime.datetime(2023, 1, 2, 11, 30),
            'lieu': '',
            'local_deliberation': '',
            'resume_annonce': '',
            'photo_annonce': [uuid.uuid4()],
        }
        response = self.client.put(
            self.url,
            data=new_data,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.doctorate.refresh_from_db()

        self.assertEqual(self.doctorate.status, ChoixStatutParcoursDoctoral.SOUTENANCE_PUBLIQUE_SOUMISE.name)
        self.assertEqual(self.doctorate.defense_language, self.language)
        self.assertEqual(self.doctorate.defense_datetime, new_data['date_heure'])
        self.assertEqual(self.doctorate.defense_place, '')
        self.assertEqual(self.doctorate.defense_deliberation_room, '')
        self.assertEqual(self.doctorate.announcement_summary, '')
        self.assertEqual(self.doctorate.announcement_photo, [uuid.UUID('4bdffb42-552d-415d-9e4c-725f10dce228')])

        historic_entries = HistoryEntry.objects.filter(object_uuid=self.doctorate.uuid)
        self.assertEqual(len(historic_entries), 1)

    def test_edit_a_known_private_defense_with_invalid_data(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        invalid_message = gettext('Public defense not completed.')

        response = self.client.put(
            self.url,
            data={
                **self.data,
                'langue': '',
            },
        )

        json_response = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors_messages = json_response.get('non_field_errors', [])
        self.assertEqual(len(errors_messages), 1)
        self.assertEqual(errors_messages[0]['status_code'], SoutenancePubliqueNonCompleteeException.status_code)

        response = self.client.put(
            self.url,
            data={
                **self.data,
                'date_heure': None,
            },
        )

        json_response = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors_messages = json_response.get('non_field_errors', [])
        self.assertEqual(len(errors_messages), 1)
        self.assertEqual(errors_messages[0]['status_code'], SoutenancePubliqueNonCompleteeException.status_code)

        response = self.client.put(
            self.url,
            data={
                **self.data,
                'photo_annonce': [],
            },
        )

        json_response = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors_messages = json_response.get('non_field_errors', [])
        self.assertEqual(len(errors_messages), 1)
        self.assertEqual(errors_messages[0]['status_code'], SoutenancePubliqueNonCompleteeException.status_code)
