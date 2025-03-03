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

from infrastructure.messages_bus import message_bus_instance
from osis_common.utils.htmx import HtmxMixin
from parcours_doctoral.ddd.commands import ListerDocumentsQuery
from parcours_doctoral.forms.document import FreeDocumentCreationForm
from parcours_doctoral.views.mixins import ParcoursDoctoralViewMixin

__all__ = [
    'DocumentsView',
]

__namespace__ = None


class DocumentsView(HtmxMixin, ParcoursDoctoralViewMixin, TemplateView):
    urlpatterns = 'documents'
    template_name = 'parcours_doctoral/details/documents.html'
    htmx_template_name = 'parcours_doctoral/document/list.html'
    permission_required = 'parcours_doctoral.view_documents'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['documents_by_section'] = message_bus_instance.invoke(
            ListerDocumentsQuery(uuid_parcours_doctoral=self.parcours_doctoral_uuid)
        )

        context['create_form'] = FreeDocumentCreationForm()

        return context
