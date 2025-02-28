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
from django.urls import reverse
from rest_framework import status

from base.forms.utils import FIELD_REQUIRED_MESSAGE
from parcours_doctoral.ddd.domain.model.document import TypeDocument
from parcours_doctoral.models import Document
from parcours_doctoral.tests.views.document import DocumentBaseTestCase


class DocumentCreationViewTestCase(DocumentBaseTestCase):
    base_url = 'parcours_doctoral:document:create'

    def setUp(self):
        super().setUp()
        self.url = reverse(self.base_url, args=[str(self.doctorate.uuid)])

    def test_with_other_manager(self):
        self.client.force_login(user=self.other_manager.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_form(self):
        self.client.force_login(user=self.manager.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        create_form = response.context.get('create_form')
        self.assertIsNotNone(create_form)
        self.assertEqual(create_form['file'].value(), [])
        self.assertEqual(create_form['file_name'].value(), None)

    def test_post_invalid_form(self):
        self.client.force_login(user=self.manager.user)

        response = self.client.post(self.url, data={})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        create_form = response.context.get('create_form')
        self.assertIsNotNone(create_form)

        self.assertFalse(create_form.is_valid())

        self.assertIn(FIELD_REQUIRED_MESSAGE, create_form.errors.get('file_name', []))
        self.assertIn(self.file_missing_message, create_form.errors.get('file', []))

    @freezegun.freeze_time('2022-01-01')
    def test_post_valid_form(self):
        self.client.force_login(user=self.manager.user)

        file_uuid = uuid.uuid4()

        response = self.client.post(
            self.url,
            data={
                'file_name': 'My new document',
                'file_0': [file_uuid],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        document = Document.objects.filter(related_doctorate=self.doctorate)

        self.assertEqual(len(document), 1)

        document = document[0]

        self.assertEqual(document.name, 'My new document')
        self.assertEqual(document.document_type, TypeDocument.LIBRE.name)
        self.assertEqual(document.related_doctorate, self.doctorate)
        self.assertEqual(document.updated_by, self.manager)
        self.assertEqual(document.updated_at, datetime.datetime(2022, 1, 1))
        self.assertEqual(document.file, [file_uuid])

    @freezegun.freeze_time('2022-01-01')
    def test_post_valid_htmx_form(self):
        self.client.force_login(user=self.manager.user)

        file_uuid = uuid.uuid4()

        response = self.client.post(
            self.url,
            data={
                'file_name': 'My new document',
                'file_0': [file_uuid],
            },
            HTTP_HX_REQUEST='true',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        created_form = response.context.get('create_form')
        self.assertIsNotNone(created_form)
        self.assertFalse(created_form.is_bound)

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
