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

from django.urls import reverse
from rest_framework import status

from parcours_doctoral.ddd.domain.model.document import TypeDocument
from parcours_doctoral.tests.factories.document import DocumentFactory
from parcours_doctoral.tests.views.document import DocumentBaseTestCase


class DocumentDetailsViewTestCase(DocumentBaseTestCase):
    base_url = 'parcours_doctoral:document:details'
    with_existing_document = True

    def setUp(self):
        super().setUp()
        patcher = patch("parcours_doctoral.views.document.details.get_remote_token", return_value='token')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "parcours_doctoral.views.document.details.get_remote_metadata",
            return_value=self.default_metadata,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_get_free_document(self):
        document = DocumentFactory(
            related_doctorate=self.doctorate,
            updated_by=self.other_manager,
            document_type=TypeDocument.LIBRE.name,
            name='My document',
        )

        url = (
            reverse(
                self.base_url,
                kwargs={
                    'uuid': self.doctorate.uuid,
                    'document_type': document.document_type,
                    'uuid_document': document.file[0],
                },
            )
            + '?document_identifier='
            + str(document.uuid)
        )

        self.client.force_login(user=self.other_manager.user)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(user=self.manager.user)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.context.get('document_uuid'), document.file[0])
        self.assertEqual(response.context.get('document_identifier'), str(document.uuid))
        self.assertEqual(response.context.get('document_token'), 'token')
        self.assertEqual(response.context.get('document_metadata'), self.default_metadata)
        self.assertEqual(response.context.get('editable_document'), True)
        self.assertIsNotNone(response.context.get('upload_form'))

    def test_get_system_document(self):
        document = DocumentFactory(
            related_doctorate=self.doctorate,
            updated_by=self.other_manager,
            document_type=TypeDocument.SYSTEME.name,
            name='My document',
        )

        url = (
            reverse(
                self.base_url,
                kwargs={
                    'uuid': self.doctorate.uuid,
                    'document_type': document.document_type,
                    'uuid_document': document.file[0],
                },
            )
            + '?document_identifier='
            + str(document.uuid)
        )

        self.client.force_login(user=self.manager.user)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.context.get('document_uuid'), document.file[0])
        self.assertEqual(response.context.get('document_identifier'), str(document.uuid))
        self.assertEqual(response.context.get('document_token'), 'token')
        self.assertEqual(response.context.get('document_metadata'), self.default_metadata)
        self.assertIsNone(response.context.get('editable_document'))
        self.assertIsNone(response.context.get('upload_form'))

    def test_get_non_free_document(self):
        file_uuid = uuid.uuid4()
        url = reverse(
            self.base_url,
            kwargs={
                'uuid': self.doctorate.uuid,
                'document_type': TypeDocument.NON_LIBRE.name,
                'uuid_document': file_uuid,
            },
        )

        self.client.force_login(user=self.manager.user)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.context.get('document_uuid'), file_uuid)
        self.assertEqual(response.context.get('document_identifier'), None)
        self.assertEqual(response.context.get('document_token'), 'token')
        self.assertEqual(response.context.get('document_metadata'), self.default_metadata)
        self.assertIsNone(response.context.get('editable_document'))
        self.assertIsNone(response.context.get('upload_form'))
