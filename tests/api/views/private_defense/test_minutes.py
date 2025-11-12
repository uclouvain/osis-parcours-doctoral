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

import uuid
from unittest.mock import patch

from django.shortcuts import resolve_url
from django.test import override_settings
from django.utils.translation import gettext
from rest_framework import status
from rest_framework.test import APITestCase

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.user import UserFactory
from parcours_doctoral.auth.roles.jury_member import JuryMember
from parcours_doctoral.ddd.defense_privee.validators.exceptions import (
    DefensePriveeNonActiveeException,
    DefensePriveeNonTrouveeException,
)
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.jury.domain.model.enums import RoleJury
from parcours_doctoral.models import JuryActor
from parcours_doctoral.tests.factories.jury import (
    JuryActorFactory,
    JuryMemberRoleFactory,
)
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.private_defense import PrivateDefenseFactory
from parcours_doctoral.tests.factories.roles import StudentRoleFactory
from parcours_doctoral.tests.factories.supervision import PromoterFactory
from parcours_doctoral.tests.mixins import MockOsisDocumentMixin


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class PrivateDefenseMinutesAPIViewTestCase(MockOsisDocumentMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.user_with_no_role = UserFactory()
        cls.other_doctorate_student = StudentRoleFactory().person
        cls.promoter = PromoterFactory()

    def setUp(self):
        super().setUp()

        # Mock osis-document
        patcher = patch(
            'parcours_doctoral.exports.private_defense_minutes_canvas.get_remote_token',
            return_value='b-token',
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        # Mock weasyprint
        patcher = patch('parcours_doctoral.exports.utils.get_pdf_from_template', return_value=b'some content')
        patcher.start()
        self.addCleanup(patcher.stop)

        # Doctorate
        self.doctorate = ParcoursDoctoralFactory(
            training__academic_year=self.academic_years[0],
            supervision_group=self.promoter.process,
            status=ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_AUTORISEE.name,
        )

        # Data
        self.private_defense = PrivateDefenseFactory(parcours_doctoral=self.doctorate)

        self.data = {
            'proces_verbal': [uuid.uuid4()],
            'uuid': str(self.private_defense.uuid),
        }

        # Targeted path
        self.url = resolve_url('parcours_doctoral_api_v1:private-defense-minutes', uuid=self.doctorate.uuid)

    def test_get_private_defense_canvas_redirect_to_the_document_url(self):
        self.client.force_authenticate(user=self.promoter.person.user)

        response = self.client.get(self.url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()

        self.assertEqual(json_response.get('url'), 'http://dummyurl/file/b-token')

        # Check saved data
        self.private_defense.refresh_from_db()

        self.assertEqual(self.private_defense.minutes_canvas, [uuid.UUID('4bdffb42-552d-415d-9e4c-725f10dce228')])

    def test_access_with_no_role(self):
        self.client.force_authenticate(self.user_with_no_role)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_access_student(self):
        self.client.force_authenticate(self.doctorate.student.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_access_with_jury_member(self):
        jury_member = JuryActorFactory(process=self.doctorate.jury_group)

        self.client.force_authenticate(user=jury_member.person.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_access_with_jury_secretary(self):
        jury_member = JuryActorFactory(process=self.doctorate.jury_group, role=RoleJury.SECRETAIRE.name)

        self.client.force_authenticate(user=jury_member.person.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.put(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_access_with_jury_president(self):
        jury_member = JuryActorFactory(process=self.doctorate.jury_group, role=RoleJury.PRESIDENT.name)

        self.client.force_authenticate(user=jury_member.person.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.put(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_with_unknown_private_defense(self):
        self.client.force_authenticate(user=self.promoter.person.user)

        response = self.client.put(
            self.url,
            data={
                **self.data,
                'uuid': str(uuid.uuid4()),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        json_response = response.json()
        self.assertIn(
            {
                'status_code': DefensePriveeNonTrouveeException.status_code,
                'detail': gettext('Private defence not found.'),
            },
            json_response.get('non_field_errors', []),
        )

    def test_edit_a_known_but_old_private_defense(self):
        self.client.force_authenticate(user=self.promoter.person.user)

        self.private_defense.current_parcours_doctoral = None
        self.private_defense.save()

        # Update of an old private defense
        response = self.client.put(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        json_response = response.json()
        self.assertIn(
            {
                'status_code': DefensePriveeNonActiveeException.status_code,
                'detail': gettext('Private defence not activated.'),
            },
            json_response.get('non_field_errors', []),
        )

    def test_edit_a_known_private_defense_with_invalid_status(self):
        self.client.force_authenticate(user=self.promoter.person.user)

        self.doctorate.status = ChoixStatutParcoursDoctoral.ADMIS.name
        self.doctorate.save()

        # Invalid status
        response = self.client.put(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        json_response = response.json()
        self.assertEqual(
            json_response.get('detail'),
            "Le doctorat doit être dans le statut 'Défense privée autorisée' pour réaliser cette action.",
        )

    def test_edit_a_known_private_defense_with_valid_data(self):
        self.client.force_authenticate(user=self.promoter.person.user)

        response = self.client.put(self.url, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.private_defense.refresh_from_db()

        self.assertEqual(self.private_defense.minutes, self.data['proces_verbal'])
