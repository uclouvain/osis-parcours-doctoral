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

import freezegun
from django.urls import reverse
from rest_framework import status

from parcours_doctoral.ddd.domain.model.document import TypeDocument
from parcours_doctoral.ddd.domain.validator.exceptions import DocumentNonTrouveException
from parcours_doctoral.models import Document
from parcours_doctoral.tests.views.document import DocumentBaseTestCase


class DocumentDeleteViewTestCase(DocumentBaseTestCase):
    base_url = 'parcours_doctoral:document:delete'
    with_existing_document = True

    def setUp(self):
        super().setUp()

        self.url = reverse(self.base_url, args=[str(self.doctorate.uuid), str(self.document.uuid)])

    def test_with_other_manager(self):
        self.client.force_login(user=self.other_manager.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_request(self):
        self.client.force_login(user=self.manager.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @freezegun.freeze_time('2022-01-01')
    def test_delete_document(self):
        self.client.force_login(user=self.manager.user)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertFalse(Document.objects.filter(related_doctorate=self.doctorate).exists())

    @freezegun.freeze_time('2022-01-01')
    def test_delete_document_with_htmx(self):
        self.client.force_login(user=self.manager.user)

        response = self.client.post(self.url, HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        upload_form = response.context.get('upload_form')
        self.assertIsNone(upload_form)

        self.assertFalse(Document.objects.filter(related_doctorate=self.doctorate).exists())

        self.assertTrue(response.context['refresh_documents'])

        documents = response.context.get('documents_by_section')
        self.assertIsNotNone(documents)

        self.assertEqual(len(documents), 2)

        self.assertIn(TypeDocument.LIBRE.value, documents)
        free_documents = documents[TypeDocument.LIBRE.value]

        self.assertEqual(len(free_documents), 0)

        self.assertIn(TypeDocument.SYSTEME.value, documents)

        self.assertIsNone(response.context.get('document_identifier'))
        self.assertIsNone(response.context.get('editable_document'))
        self.assertIsNone(response.context.get('upload_form'))
        self.assertIsNone(response.context.get('document_uuid'))
        self.assertIsNone(response.context.get('document_token'))
        self.assertIsNone(response.context.get('document_metadata'))

    def test_delete_unknown_document(self):
        self.client.force_login(user=self.manager.user)

        url = reverse(self.base_url, args=[str(self.doctorate.uuid), str(uuid.uuid4())])

        # Normal request
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        messages = [m.message for m in list(response.context['messages'])]

        self.assertIn(DocumentNonTrouveException().message, messages)

        # HTMX request
        response = self.client.post(url, HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        messages = [m.message for m in list(response.context['messages'])]

        self.assertIn(DocumentNonTrouveException().message, messages)
