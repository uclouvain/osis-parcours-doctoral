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
from unittest.mock import ANY, patch

from osis_document_components.utils import is_uuid


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

        default_uuid = '4bdffb42-552d-415d-9e4c-725f10dce228'

        # Mock osis-document
        self.confirm_remote_upload_patcher = patch('osis_document_components.services.confirm_remote_upload')
        patched = self.confirm_remote_upload_patcher.start()
        patched.side_effect = lambda token, _1, _2, _3, _4, _5: str(token) if is_uuid(token) else default_uuid
        self.addCleanup(self.confirm_remote_upload_patcher.stop)

        self.file_confirm_upload_patcher = patch('osis_document_components.fields.FileField._confirm_multiple_upload')
        patched = self.file_confirm_upload_patcher.start()
        patched.side_effect = lambda _, value, __: [uuid.UUID(str(v)) if is_uuid(v) else default_uuid for v in value]
        self.addCleanup(self.file_confirm_upload_patcher.stop)

        self.get_remote_metadata_patcher = patch('osis_document_components.services.get_remote_metadata')
        patched = self.get_remote_metadata_patcher.start()
        patched.return_value = {"name": "test.pdf", "size": 1, "mimetype": ANY}
        self.addCleanup(self.get_remote_metadata_patcher.stop)

        self.get_remote_token_patcher = patch('osis_document_components.services.get_remote_token')
        patched = self.get_remote_token_patcher.start()
        patched.return_value = 'b-token'
        self.addCleanup(self.get_remote_token_patcher.stop)

        self.save_raw_content_remotely_patcher = patch('osis_document_components.services.save_raw_content_remotely')
        patched = self.save_raw_content_remotely_patcher.start()
        patched.return_value = 'a-token'
        self.addCleanup(self.save_raw_content_remotely_patcher.stop)

        patcher = patch('osis_document_components.services.get_remote_tokens')
        patched = patcher.start()
        patched.side_effect = lambda uuids, **kwargs: {
            current_uuid: f'token-{index}' for index, current_uuid in enumerate(uuids)
        }
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document_components.services.get_several_remote_metadata')
        patched = patcher.start()
        patched.side_effect = lambda tokens: {
            token: {
                'name': 'myfile',
                'mimetype': ANY,
                'size': 1,
            }
            for token in tokens
        }
        self.addCleanup(patcher.stop)
