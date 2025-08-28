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
from typing import Optional

from django.urls import reverse
from django.views.generic import FormView
from osis_document.api.utils import get_remote_metadata, get_remote_token
from osis_document.enums import PostProcessingWanted

from base.utils.htmx import HtmxPermissionRequiredMixin
from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.commands import ListerDocumentsQuery
from parcours_doctoral.ddd.domain.model.document import TypeDocument
from parcours_doctoral.ddd.dtos.document import DocumentDTO
from parcours_doctoral.forms.document import FreeDocumentUploadForm
from parcours_doctoral.views.mixins import ParcoursDoctoralFormMixin


class DocumentFormView(HtmxPermissionRequiredMixin, ParcoursDoctoralFormMixin, FormView):
    permission_required = 'parcours_doctoral.change_documents'
    template_name = 'parcours_doctoral/document/base_htmx.html'
    load_doctorate_dto = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.document_uuid = None
        self.document_identifier = None
        self.refresh_documents = False

    def form_valid(self, form):
        self.refresh_documents = True
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if not self.refresh_documents or not self.request.htmx:
            return context

        # If the form is valid, we want to refresh the document list and the document details
        context['refresh_documents'] = True

        # Load data for the listing
        context['documents_by_section'] = message_bus_instance.invoke(
            ListerDocumentsQuery(uuid_parcours_doctoral=self.parcours_doctoral_uuid)
        )

        # Load data for the details
        if self.document_identifier:
            context['document_identifier'] = self.document_identifier

            document: Optional[DocumentDTO] = next(
                (
                    current_document
                    for section_documents in context['documents_by_section'].values()
                    for current_document in section_documents
                    if current_document.identifiant == self.document_identifier
                ),
                None,
            )

            if document:
                self.document_uuid = document.uuids_documents[0]

                if document.type == TypeDocument.LIBRE.name:
                    context['editable_document'] = True
                    context['upload_form'] = FreeDocumentUploadForm()

        if self.document_uuid:
            context['document_uuid'] = self.document_uuid
            context['document_token'] = get_remote_token(
                uuid=self.document_uuid,
                wanted_post_process=PostProcessingWanted.ORIGINAL.name,
            )
            context['document_metadata'] = get_remote_metadata(token=context['document_token'])

        return context

    def get_success_url(self):
        return reverse('parcours_doctoral:documents', args=[self.parcours_doctoral_uuid])
