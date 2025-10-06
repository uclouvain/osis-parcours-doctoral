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

from unittest.mock import patch

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings

from base.tests.factories.program_manager import ProgramManagerFactory
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.roles import StudentRoleFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class SupervisionCanvasExportViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Users
        cls.student = StudentRoleFactory().person
        cls.doctorate = ParcoursDoctoralFactory(
            student=cls.student,
        )

        cls.manager = ProgramManagerFactory(education_group=cls.doctorate.training.education_group).person.user

        # Targeted path
        cls.url = resolve_url('parcours_doctoral:supervision-canvas', uuid=cls.doctorate.uuid)

        # Mock osis-document
        cls.confirm_remote_upload_patcher = patch('osis_document_components.services.confirm_remote_upload')
        patched = cls.confirm_remote_upload_patcher.start()
        patched.return_value = '4bdffb42-552d-415d-9e4c-725f10dce228'

        cls.file_confirm_upload_patcher = patch('osis_document_components.fields.FileField._confirm_multiple_upload')
        patched = cls.file_confirm_upload_patcher.start()
        patched.side_effect = lambda _, value, __: ['4bdffb42-552d-415d-9e4c-725f10dce228'] if value else []

        cls.get_remote_metadata_patcher = patch('osis_document_components.services.get_remote_metadata')
        patched = cls.get_remote_metadata_patcher.start()
        patched.return_value = {"name": "test.pdf", "size": 1}

        cls.get_remote_token_patcher = patch('osis_document_components.services.get_remote_token')
        patched = cls.get_remote_token_patcher.start()
        patched.return_value = 'b-token'

        cls.save_raw_content_remotely_patcher = patch('osis_document_components.services.save_raw_content_remotely')
        patched = cls.save_raw_content_remotely_patcher.start()
        patched.return_value = 'a-token'

        # Mock weasyprint
        cls.weasyprint_patcher = patch('parcours_doctoral.exports.utils.get_pdf_from_template')
        patched = cls.weasyprint_patcher.start()
        patched.return_value = b'some content'

    @classmethod
    def tearDownClass(cls):
        cls.confirm_remote_upload_patcher.stop()
        cls.get_remote_metadata_patcher.stop()
        cls.get_remote_token_patcher.stop()
        cls.save_raw_content_remotely_patcher.stop()
        cls.file_confirm_upload_patcher.stop()
        cls.weasyprint_patcher.stop()
        super().tearDownClass()

    def test_redirect_to_canvas_url(self):
        self.client.force_login(user=self.manager)

        response = self.client.get(self.url)

        self.assertRedirects(
            response=response,
            expected_url='http://dummyurl/file/a-token',
            fetch_redirect_response=False,
        )
