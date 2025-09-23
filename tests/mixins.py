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
from unittest.mock import patch


class CheckActionLinksMixin:
    def assertActionLinks(self, links, allowed_actions, forbidden_actions):
        self.assertCountEqual(list(links), allowed_actions + forbidden_actions)

        for action in allowed_actions:
            self.assertTrue('url' in links[action], '{} is not allowed'.format(action))

        for action in forbidden_actions:
            self.assertTrue('error' in links[action], '{} is allowed'.format(action))


class MockOsisDocumentMixin:
    def setUp(self):
        super().setUp()

        # Mock osis-document
        self.confirm_remote_upload_patcher = patch('osis_document_components.services.confirm_remote_upload')
        patched = self.confirm_remote_upload_patcher.start()
        patched.return_value = '4bdffb42-552d-415d-9e4c-725f10dce228'

        self.file_confirm_upload_patcher = patch('osis_document_components.fields.FileField._confirm_multiple_upload')
        patched = self.file_confirm_upload_patcher.start()
        patched.side_effect = lambda _, value, __: ['4bdffb42-552d-415d-9e4c-725f10dce228'] if value else []

        self.get_remote_metadata_patcher = patch('osis_document_components.services.get_remote_metadata')
        patched = self.get_remote_metadata_patcher.start()
        patched.return_value = {"name": "test.pdf", "size": 1}

        self.get_remote_token_patcher = patch('osis_document_components.services.get_remote_token')
        patched = self.get_remote_token_patcher.start()
        patched.return_value = 'b-token'

        self.save_raw_content_remotely_patcher = patch('osis_document_components.services.save_raw_content_remotely')
        patched = self.save_raw_content_remotely_patcher.start()
        patched.return_value = 'a-token'
