# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
from typing import Optional

import freezegun
from django.contrib.auth.models import User
from django.shortcuts import resolve_url
from rest_framework import status
from rest_framework.test import APITestCase

from parcours_doctoral.tests.factories.roles import StudentRoleFactory
from parcours_doctoral.tests.factories.supervision import PromoterFactory
from base.models.enums.entity_type import EntityType
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory


class ParcoursDoctoralAPIViewTestCase(APITestCase):
    parcours_doctoral: Optional[ParcoursDoctoralFactory] = None
    other_parcours_doctoral: Optional[ParcoursDoctoralFactory] = None
    commission: Optional[EntityVersionFactory] = None
    sector: Optional[EntityVersionFactory] = None
    student: Optional[StudentRoleFactory] = None
    other_student: Optional[StudentRoleFactory] = None
    no_role_user: Optional[User] = None
    parcours_doctoral_url: Optional[str] = None
    other_parcours_doctoral_url: Optional[str] = None

    @classmethod
    @freezegun.freeze_time('2023-01-01')
    def setUpTestData(cls):
        # Create supervision group members
        promoter = PromoterFactory()

        # Create parcours_doctoral management entity
        root = EntityVersionFactory(parent=None).entity
        cls.sector = EntityVersionFactory(
            parent=root,
            entity_type=EntityType.SECTOR.name,
            acronym='SST',
        ).entity
        cls.commission = EntityVersionFactory(
            parent=cls.sector,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        ).entity
        cls.parcours_doctoral = ParcoursDoctoralFactory(
            training__management_entity=cls.commission,
            supervision_group=promoter.process,
            training__enrollment_campus__name='Mons',
        )
        cls.other_parcours_doctoral = ParcoursDoctoralFactory(
            training__management_entity=cls.commission,
        )
        # Users
        cls.student = cls.parcours_doctoral.student
        cls.other_student = cls.other_parcours_doctoral.student
        cls.no_role_user = PersonFactory().user

        cls.parcours_doctoral_url = resolve_url('parcours_doctoral_api_v1:parcours_doctoral', uuid=cls.parcours_doctoral.uuid)
        cls.other_parcours_doctoral_url = resolve_url('parcours_doctoral_api_v1:parcours_doctoral', uuid=cls.other_parcours_doctoral.uuid)

    @freezegun.freeze_time('2023-01-01')
    def test_get_parcours_doctoral_student(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.parcours_doctoral_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        json_response = response.json()

        # Check parcours_doctoral links
        self.assertTrue('links' in json_response)
        allowed_actions = [
        ]
        forbidden_actions = [
            'retrieve_cotutelle',
            'retrieve_supervision',
            'retrieve_project',
        ]
        self.assertCountEqual(json_response['links'], allowed_actions + forbidden_actions)
        for action in allowed_actions:
            # Check the url
            self.assertTrue('url' in json_response['links'][action], '{} is not allowed'.format(action))
            # Check the method type
            self.assertTrue('method' in json_response['links'][action])

        # Check parcours_doctoral properties
        self.assertEqual(json_response['uuid'], str(self.parcours_doctoral.uuid))
        self.assertEqual(json_response['reference'], f'M-CDA22-{str(self.parcours_doctoral)}')
        self.assertEqual(json_response['statut'], self.parcours_doctoral.status)
        self.assertEqual(json_response['formation']['sigle'], self.parcours_doctoral.parcours_doctoral.acronym)
        self.assertEqual(json_response['formation']['annee'], self.parcours_doctoral.parcours_doctoral.academic_year.year)
        self.assertEqual(json_response['formation']['intitule'], self.parcours_doctoral.parcours_doctoral.title)
        self.assertEqual(json_response['matricule_doctorant'], self.parcours_doctoral.student.global_id)
        self.assertEqual(json_response['prenom_doctorant'], self.parcours_doctoral.student.first_name)
        self.assertEqual(json_response['nom_doctorant'], self.parcours_doctoral.student.last_name)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.student.user)
        methods_not_allowed = [
            'delete',
            'put',
            'patch',
            'post',
        ]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.parcours_doctoral_url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_parcours_doctoral_other_student(self):
        self.client.force_authenticate(user=self.other_student.user)
        response = self.client.get(self.parcours_doctoral_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
