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
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from base.tests.factories.academic_year import AcademicYearFactory
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.private_defense import PrivateDefenseFactory
from parcours_doctoral.tests.factories.supervision import PromoterFactory
from parcours_doctoral.tests.mixins import MockOsisDocumentMixin


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class PrivateDefenseMinutesAPIViewTestCase(MockOsisDocumentMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.promoter = PromoterFactory()
        cls.doctorate = ParcoursDoctoralFactory(
            training__academic_year=academic_years[0],
            supervision_group=cls.promoter.process,
        )
        cls.private_defense = PrivateDefenseFactory(parcours_doctoral=cls.doctorate)

        # Targeted path
        cls.url = resolve_url('parcours_doctoral_api_v1:private-defense-minutes', uuid=cls.doctorate.uuid)

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
