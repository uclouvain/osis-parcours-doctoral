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
from rest_framework.status import HTTP_302_FOUND

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.mixins import MockOsisDocumentMixin


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class PublicDefenseMinutesCanvasViewTestCase(MockOsisDocumentMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.doctorate = ParcoursDoctoralFactory(training__academic_year=academic_years[0])

        cls.manager = ProgramManagerFactory(education_group=cls.doctorate.training.education_group).person.user

        # Targeted path
        cls.url = resolve_url('parcours_doctoral:public-defense-minutes-canvas', uuid=cls.doctorate.uuid)

    def setUp(self):
        super().setUp()

        # Mock osis-document
        patcher = patch(
            'parcours_doctoral.exports.public_defense_minutes_canvas.get_remote_token',
            return_value='b-token',
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        # Mock weasyprint
        patcher = patch('parcours_doctoral.exports.utils.get_pdf_from_template', return_value=b'some content')
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_get_public_defense_canvas_redirect_to_the_document_url(self):
        self.client.force_login(user=self.manager)

        response = self.client.get(self.url)

        # Check response
        self.assertEqual(response.status_code, HTTP_302_FOUND)
        self.assertRedirects(
            response=response,
            expected_url='http://dummyurl/file/b-token',
            fetch_redirect_response=False,
        )

        # Check saved data
        self.doctorate.refresh_from_db()

        self.assertEqual(self.doctorate.defense_minutes_canvas, [uuid.UUID('4bdffb42-552d-415d-9e4c-725f10dce228')])
