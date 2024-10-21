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
from admission.tests.factories.scholarship import (
    DoctorateScholarshipFactory,
    DoubleDegreeScholarshipFactory,
    ErasmusMundusScholarshipFactory,
    InternationalScholarshipFactory,
)
from base.tests.factories.user import UserFactory
from django.shortcuts import resolve_url
from rest_framework.test import APITestCase


class AutocompleteScholarshipViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.scholarships = [
            DoubleDegreeScholarshipFactory(short_name='DDS-1', long_name='Dual degree scholarship 1'),
            InternationalScholarshipFactory(short_name='IS-1bis', long_name='International scholarship 1bis'),
            InternationalScholarshipFactory(short_name='IS-2bis', long_name='International scholarship 2bis'),
            InternationalScholarshipFactory(short_name='AIS', long_name=''),
            ErasmusMundusScholarshipFactory(short_name='EMS-2', long_name='Erasmus Mundus scholarship 2'),
            DoctorateScholarshipFactory(short_name='DS-2', long_name='Doctorate scholarship 2'),
            DoctorateScholarshipFactory(short_name='DS-1', long_name='Doctorate scholarship 1'),
            DoctorateScholarshipFactory(short_name='DS-0', long_name='Doctorate scholarship 0', disabled=True),
        ]
        cls.user = UserFactory()
        cls.base_url = resolve_url('parcours_doctoral_api_v1:scholarships')

    def test_autocomplete_scholarship_without_search_parameter(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            self.base_url,
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['count'], 2)

        self.assertEqual(
            response.json()['results'],
            [
                {
                    'uuid': str(scholarship.uuid),
                    'short_name': scholarship.short_name,
                    'long_name': scholarship.long_name,
                }
                for scholarship in [
                    self.scholarships[6],
                    self.scholarships[5],
                ]
            ],
        )

    def test_autocomplete_scholarship_with_search(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            self.base_url,
            format='json',
            data={
                'search': '2',
            },
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['count'], 1)

        self.assertEqual(
            response.json()['results'],
            [
                {
                    'uuid': str(scholarship.uuid),
                    'short_name': scholarship.short_name,
                    'long_name': scholarship.long_name,
                }
                for scholarship in [
                    self.scholarships[5],
                ]
            ],
        )
