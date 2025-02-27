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
from unittest.mock import patch

import freezegun
from django.test import override_settings
from django.urls import reverse
from rest_framework import status

from parcours_doctoral.ddd.domain.model.document import TypeDocument
from parcours_doctoral.models import Document
from parcours_doctoral.tests.views.document import DocumentBaseTestCase


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class DocumentArchiveCreationViewTestCase(DocumentBaseTestCase):
    base_url = 'parcours_doctoral:document:create-archive'

    def setUp(self):
        super().setUp()

        self.created_archive_uuid = str(uuid.uuid4())

        patcher = patch(
            "parcours_doctoral.exports.archive.parcours_doctoral_generate_pdf",
            return_value=self.created_archive_uuid,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        self.url = reverse(self.base_url, args=[str(self.doctorate.uuid)])

    def test_with_other_manager(self):
        self.client.force_login(user=self.other_manager.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @freezegun.freeze_time('2022-01-01')
    def test_post(self):
        self.client.force_login(user=self.manager.user)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        document = Document.objects.filter(related_doctorate=self.doctorate)

        self.assertEqual(len(document), 1)

        document = document[0]

        self.assertEqual(document.name, 'Archive')
        self.assertEqual(document.document_type, TypeDocument.SYSTEME.name)
        self.assertEqual(document.related_doctorate, self.doctorate)
        self.assertEqual(document.updated_by, self.manager)
        self.assertEqual(document.updated_at, datetime.datetime(2022, 1, 1))
        self.assertEqual(str(document.file[0]), self.created_archive_uuid)

    @freezegun.freeze_time('2022-01-01')
    def test_htmx_post(self):
        self.client.force_login(user=self.manager.user)

        response = self.client.post(self.url, HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        documents = Document.objects.filter(related_doctorate=self.doctorate)

        self.assertEqual(len(documents), 1)

        document = documents[0]

        self.assertTrue(response.context['refresh_documents'])

        documents = response.context.get('documents_by_section')
        self.assertIsNotNone(documents)

        self.assertEqual(len(documents), 2)

        self.assertIn(TypeDocument.LIBRE.value, documents)
        free_documents = documents[TypeDocument.LIBRE.value]

        self.assertEqual(len(free_documents), 0)

        self.assertIn(TypeDocument.SYSTEME.value, documents)
        system_documents = documents[TypeDocument.SYSTEME.value]

        self.assertEqual(len(system_documents), 1)
        self.assertEqual(system_documents[0].identifiant, str(document.uuid))

        self.assertEqual(response.context.get('document_identifier'), str(document.uuid))
        self.assertIsNone(response.context.get('editable_document'))
        self.assertIsNone(response.context.get('upload_form'))
        self.assertEqual(str(document.file[0]), str(self.created_archive_uuid))
        self.assertEqual(response.context.get('document_uuid'), document.file[0])
        self.assertEqual(response.context.get('document_token'), 'token')
        self.assertEqual(response.context.get('document_metadata'), self.default_metadata)
