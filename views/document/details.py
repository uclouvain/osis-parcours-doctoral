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
from django.views.generic import TemplateView
from osis_document_components.services import get_remote_metadata, get_remote_token
from osis_document_components.enums import PostProcessingWanted

from parcours_doctoral.ddd.domain.model.document import TypeDocument
from parcours_doctoral.forms.document import FreeDocumentUploadForm
from parcours_doctoral.views.mixins import ParcoursDoctoralViewMixin

__all__ = [
    'DocumentDetailsView',
]

__namespace__ = None


class DocumentDetailsView(ParcoursDoctoralViewMixin, TemplateView):
    urlpatterns = {'details': '<str:document_type>/<uuid:uuid_document>'}
    template_name = 'parcours_doctoral/document/details.html'
    htmx_template_name = 'parcours_doctoral/document/details.html'
    permission_required = 'parcours_doctoral.view_documents'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        document_type = self.kwargs['document_type']
        document_uuid = self.kwargs['uuid_document']

        context['document_uuid'] = document_uuid
        context['document_identifier'] = self.request.GET.get('document_identifier')
        context['document_token'] = get_remote_token(
            uuid=document_uuid,
            wanted_post_process=PostProcessingWanted.ORIGINAL.name,
        )
        context['document_metadata'] = get_remote_metadata(token=context['document_token'])

        if document_type == TypeDocument.LIBRE.name and self.request.user.has_perm(
            perm='parcours_doctoral.change_documents',
            obj=self.get_permission_object(),
        ):
            context['editable_document'] = True
            context['upload_form'] = FreeDocumentUploadForm()

        return context
