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

from infrastructure.messages_bus import message_bus_instance
from osis_common.ddd.interface import BusinessException
from parcours_doctoral.ddd.commands import ModifierDocumentCommand
from parcours_doctoral.forms.document import FreeDocumentUploadForm
from parcours_doctoral.views.document.mixins import DocumentFormView

__all__ = [
    'DocumentUploadView',
]

__namespace__ = None


class DocumentUploadView(DocumentFormView):
    urlpatterns = {'upload': '<uuid:document_identifier>'}
    template_name = 'parcours_doctoral/document/upload.html'
    form_class = FreeDocumentUploadForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.setdefault('upload_form', context.pop('form'))
        context.setdefault('document_identifier', self.kwargs['document_identifier'])

        return context

    def form_valid(self, form):
        try:
            self.document_identifier = message_bus_instance.invoke(
                ModifierDocumentCommand(
                    uuid_parcours_doctoral=self.parcours_doctoral_uuid,
                    identifiant=str(self.kwargs['document_identifier']),
                    uuids_documents=form.cleaned_data['file'],
                    auteur=self.request.user.person.global_id,
                )
            ).identifiant

        except BusinessException as exception:
            self.message_on_failure = exception.message
            response = self.form_invalid(form)
            response.status_code = 400
            return response

        self.template_name = 'parcours_doctoral/document/base_htmx.html'

        return super().form_valid(form)
