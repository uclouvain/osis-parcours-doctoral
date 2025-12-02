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
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.jury.domain.model.enums import FormuleDefense
from parcours_doctoral.models import ActorType, ParcoursDoctoral
from parcours_doctoral.models.private_defense import PrivateDefense
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.private_defense import PrivateDefenseFactory
from parcours_doctoral.tests.factories.roles import StudentRoleFactory
from parcours_doctoral.tests.mixins import MockOsisDocumentMixin
from reference.tests.factories.language import LanguageFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class PrivatePublicDefensesAPIViewTestCase(MockOsisDocumentMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_with_no_role = UserFactory()
        cls.doctorate_student = StudentRoleFactory().person
        cls.other_doctorate_student = StudentRoleFactory().person

        cls.other_doctorate = ParcoursDoctoralFactory(
            student=cls.other_doctorate_student,
            thesis_proposed_title='T2',
        )

        cls.language = LanguageFactory()
        cls.other_language = LanguageFactory()

        cls.data = {
            'titre_these': 'New thesis title',
            'date_heure_defense_privee': '2025-09-09T10:00:00',
            'lieu_defense_privee': 'Private defense location',
            'date_envoi_manuscrit': '2025-08-08',
            'langue_soutenance_publique': cls.language.code,
            'date_heure_soutenance_publique': '2025-09-10T11:00:00',
            'lieu_soutenance_publique': 'Public defense location',
            'local_deliberation': 'L1',
            'resume_annonce': 'Summary of the public defense',
            'photo_annonce': [uuid.uuid4()],
        }

        cls.base_namespace = 'parcours_doctoral_api_v1:private-public-defenses'

    def setUp(self):
        super().setUp()

        self.doctorate: ParcoursDoctoral = ParcoursDoctoralFactory(
            student=self.doctorate_student,
            thesis_proposed_title='T1',
            status=ChoixStatutParcoursDoctoral.RECEVABILITE_REUSSIE.name,
            defense_method=FormuleDefense.FORMULE_2.name,
        )

        self.private_defense: PrivateDefense = PrivateDefenseFactory(parcours_doctoral=self.doctorate)

        self.url = resolve_url(
            self.base_namespace,
            uuid=self.doctorate.uuid,
        )

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        methods_not_allowed = [
            'delete',
            'patch',
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

    def test_edit_with_invalid_status(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        self.doctorate.status = ChoixStatutParcoursDoctoral.ADMIS.name
        self.doctorate.save()

        # Invalid status
        response = self.client.put(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        json_response = response.json()
        self.assertEqual(json_response.get('detail'), gettext('The public defence is not in progress'))

    def test_edit_with_valid_data(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        # First submission with valid data
        response = self.client.put(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.private_defense.refresh_from_db()
        self.doctorate.refresh_from_db()

        self.assertEqual(
            self.doctorate.status,
            ChoixStatutParcoursDoctoral.DEFENSE_ET_SOUTENANCE_SOUMISES.name,
        )
        self.assertEqual(self.doctorate.thesis_proposed_title, self.data['titre_these'])
        self.assertEqual(self.doctorate.defense_language, self.language)
        self.assertEqual(
            self.doctorate.defense_datetime,
            datetime.datetime.fromisoformat(self.data['date_heure_soutenance_publique']),
        )
        self.assertEqual(self.doctorate.defense_place, self.data['lieu_soutenance_publique'])
        self.assertEqual(self.doctorate.defense_deliberation_room, self.data['local_deliberation'])
        self.assertEqual(self.doctorate.announcement_summary, self.data['resume_annonce'])
        self.assertEqual(self.doctorate.announcement_photo, self.data['photo_annonce'])

        self.assertEqual(
            self.private_defense.datetime,
            datetime.datetime.fromisoformat(self.data['date_heure_defense_privee']),
        )
        self.assertEqual(self.private_defense.place, self.data['lieu_defense_privee'])
        self.assertEqual(
            self.private_defense.manuscript_submission_date,
            datetime.date.fromisoformat(self.data['date_envoi_manuscrit']),
        )

        historic_entries = HistoryEntry.objects.filter(object_uuid=self.doctorate.uuid)
        self.assertEqual(len(historic_entries), 1)
        self.assertCountEqual(
            historic_entries[0].tags,
            ["parcours_doctoral", "private-public-defenses", "status-changed"],
        )

        # Newer submission
        new_data = {
            'titre_these': 'New thesis title 2',
            'date_heure_defense_privee': '2026-09-09T10:00:00',
            'lieu_defense_privee': 'Private defense location 2',
            'date_envoi_manuscrit': '2026-08-08',
            'langue_soutenance_publique': self.other_language.code,
            'date_heure_soutenance_publique': '2026-09-10T11:00:00',
            'lieu_soutenance_publique': 'Public defense location 2',
            'local_deliberation': 'L2',
            'resume_annonce': 'Summary of the public defense 2',
            'photo_annonce': [uuid.uuid4()],
        }

        response = self.client.put(self.url, data=new_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.private_defense.refresh_from_db()
        self.doctorate.refresh_from_db()

        self.assertEqual(
            self.doctorate.status,
            ChoixStatutParcoursDoctoral.DEFENSE_ET_SOUTENANCE_SOUMISES.name,
        )
        self.assertEqual(self.doctorate.thesis_proposed_title, new_data['titre_these'])
        self.assertEqual(self.doctorate.defense_language, self.other_language)
        self.assertEqual(
            self.doctorate.defense_datetime,
            datetime.datetime.fromisoformat(new_data['date_heure_soutenance_publique']),
        )
        self.assertEqual(self.doctorate.defense_place, new_data['lieu_soutenance_publique'])
        self.assertEqual(self.doctorate.defense_deliberation_room, new_data['local_deliberation'])
        self.assertEqual(self.doctorate.announcement_summary, new_data['resume_annonce'])
        self.assertEqual(self.doctorate.announcement_photo, new_data['photo_annonce'])

        self.assertEqual(
            self.private_defense.datetime,
            datetime.datetime.fromisoformat(new_data['date_heure_defense_privee']),
        )
        self.assertEqual(self.private_defense.place, new_data['lieu_defense_privee'])
        self.assertEqual(
            self.private_defense.manuscript_submission_date,
            datetime.date.fromisoformat(new_data['date_envoi_manuscrit']),
        )

        historic_entries = HistoryEntry.objects.filter(object_uuid=self.doctorate.uuid)
        self.assertEqual(len(historic_entries), 1)

    def test_edit_with_invalid_data(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        # Invalid data
        response = self.client.put(
            self.url,
            data={
                'titre_these': '',
                'langue_soutenance_publique': '',
                'date_heure_defense_privee': '',
                'lieu_defense_privee': '',
                'date_heure_soutenance_publique': '',
                'lieu_soutenance_publique': '',
                'date_envoi_manuscrit': '',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_minutes(self):
        promoter = self.doctorate.supervision_group.actors.filter(
            parcoursdoctoralsupervisionactor__type=ActorType.PROMOTER.name
        ).first()
        self.client.force_authenticate(user=promoter.person.user)

        self.doctorate.status = ChoixStatutParcoursDoctoral.DEFENSE_ET_SOUTENANCE_AUTORISEES.name
        self.doctorate.save()

        data = {
            'proces_verbal_defense_privee': [uuid.uuid4()],
            'proces_verbal_soutenance_publique': [uuid.uuid4()],
        }

        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.doctorate.refresh_from_db()
        self.private_defense.refresh_from_db()

        self.assertEqual(self.doctorate.defense_minutes, data['proces_verbal_soutenance_publique'])
        self.assertEqual(self.private_defense.minutes, data['proces_verbal_defense_privee'])

    def test_submit_minutes_with_invalid_status(self):
        promoter = self.doctorate.supervision_group.actors.filter(
            parcoursdoctoralsupervisionactor__type=ActorType.PROMOTER.name
        ).first()
        self.client.force_authenticate(user=promoter.person.user)

        self.doctorate.status = ChoixStatutParcoursDoctoral.ADMIS.name
        self.doctorate.save()

        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        json_response = response.json()
        self.assertEqual(
            json_response.get('detail'),
            "Le doctorat doit être dans le statut 'Défense/Soutenance autorisées' pour réaliser cette action.",
        )
