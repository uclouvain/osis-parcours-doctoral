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

import freezegun
from django.test import override_settings
from django.urls import reverse
from rest_framework import status

from parcours_doctoral.ddd.domain.model.document import TypeDocument
from parcours_doctoral.ddd.domain.validator.exceptions import DocumentNonTrouveException
from parcours_doctoral.models import Document
from parcours_doctoral.tests.views.document import DocumentBaseTestCase


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class DocumentUploadViewTestCase(DocumentBaseTestCase):
    base_url = 'parcours_doctoral:document:upload'
    with_existing_document = True

    def setUp(self):
        super().setUp()

        self.url = reverse(self.base_url, args=[str(self.doctorate.uuid), str(self.document.uuid)])

    def test_with_other_manager(self):
        self.client.force_login(user=self.other_manager.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_form(self):
        self.client.force_login(user=self.manager.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        upload_form = response.context.get('upload_form')
        self.assertIsNotNone(upload_form)

        self.assertEqual(upload_form['file'].value(), [])

    def test_post_invalid_form(self):
        self.client.force_login(user=self.manager.user)

        response = self.client.post(self.url, data={})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        upload_form = response.context.get('upload_form')
        self.assertIsNotNone(upload_form)

        self.assertFalse(upload_form.is_valid())

        self.assertIn(self.file_missing_message, upload_form.errors.get('file', []))

    @freezegun.freeze_time('2022-01-01')
    def test_post_valid_form(self):
        self.client.force_login(user=self.manager.user)

        file_uuid = uuid.uuid4()

        response = self.client.post(
            self.url,
            data={
                'file_0': [file_uuid],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.document.refresh_from_db()

        self.assertEqual(self.document.name, 'My document')
        self.assertEqual(self.document.document_type, TypeDocument.LIBRE.name)
        self.assertEqual(self.document.related_doctorate, self.doctorate)
        self.assertEqual(self.document.updated_by, self.manager)
        self.assertEqual(self.document.updated_at, datetime.datetime(2022, 1, 1))
        self.assertEqual(self.document.file, [file_uuid])

    @freezegun.freeze_time('2022-01-01')
    def test_post_valid_htmx_form(self):
        self.client.force_login(user=self.manager.user)

        file_uuid = uuid.uuid4()

        response = self.client.post(
            self.url,
            data={
                'file_0': [file_uuid],
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        upload_form = response.context.get('upload_form')
        self.assertIsNotNone(upload_form)
        self.assertFalse(upload_form.is_bound)

        documents = Document.objects.filter(related_doctorate=self.doctorate)

        self.assertEqual(len(documents), 1)

        document = documents[0]

        self.assertTrue(response.context['refresh_documents'])

        documents = response.context.get('documents_by_section')
        self.assertIsNotNone(documents)

        self.assertEqual(len(documents), 2)

        self.assertIn(TypeDocument.LIBRE.value, documents)
        free_documents = documents[TypeDocument.LIBRE.value]

        self.assertEqual(len(free_documents), 1)
        self.assertEqual(free_documents[0].identifiant, str(document.uuid))

        self.assertIn(TypeDocument.SYSTEME.value, documents)

        self.assertEqual(response.context.get('document_identifier'), str(document.uuid))
        self.assertTrue(response.context.get('editable_document'))
        self.assertIsNotNone(response.context.get('upload_form'))
        self.assertEqual(document.file[0], file_uuid)
        self.assertEqual(response.context.get('document_uuid'), document.file[0])
        self.assertEqual(response.context.get('document_token'), 'token')
        self.assertEqual(response.context.get('document_metadata'), self.default_metadata)

    def test_post_valid_form_but_for_unknown_document(self):
        self.client.force_login(user=self.manager.user)

        url = reverse(self.base_url, args=[str(self.doctorate.uuid), str(uuid.uuid4())])

        # Normal request
        response = self.client.post(
            url,
            data={
                'file_0': [uuid.uuid4()],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        messages = [m.message for m in list(response.context['messages'])]

        self.assertIn(DocumentNonTrouveException().message, messages)

        # HTMX request
        response = self.client.post(
            url,
            data={
                'file_0': [uuid.uuid4()],
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        messages = [m.message for m in list(response.context['messages'])]

        self.assertIn(DocumentNonTrouveException().message, messages)
