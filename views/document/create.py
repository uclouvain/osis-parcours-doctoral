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
from parcours_doctoral.ddd.commands import InitialiserDocumentCommand
from parcours_doctoral.ddd.domain.model.document import TypeDocument
from parcours_doctoral.forms.document import FreeDocumentCreationForm
from parcours_doctoral.views.document.mixins import DocumentFormView

__all__ = [
    'DocumentCreationView',
]

__namespace__ = None


class DocumentCreationView(DocumentFormView):
    urlpatterns = 'create'
    template_name = 'parcours_doctoral/document/create.html'
    form_class = FreeDocumentCreationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('create_form', context.pop('form'))
        return context

    def form_valid(self, form):
        self.document_identifier = message_bus_instance.invoke(
            InitialiserDocumentCommand(
                uuid_parcours_doctoral=self.parcours_doctoral_uuid,
                uuids_documents=form.cleaned_data['file'],
                libelle=form.cleaned_data['file_name'],
                type_document=TypeDocument.LIBRE.name,
                auteur=self.request.user.person.global_id,
            )
        ).identifiant

        return super().form_valid(FreeDocumentCreationForm())
