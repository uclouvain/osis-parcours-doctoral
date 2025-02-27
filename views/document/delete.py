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

from django.forms.forms import Form

from infrastructure.messages_bus import message_bus_instance
from osis_common.ddd.interface import BusinessException
from parcours_doctoral.ddd.commands import SupprimerDocumentCommand
from parcours_doctoral.views.document.mixins import DocumentFormView

__all__ = [
    'DocumentDeletionView',
]

__namespace__ = None


class DocumentDeletionView(DocumentFormView):
    urlpatterns = {'delete': '<uuid:document_identifier>/delete'}
    form_class = Form

    def form_valid(self, form):
        try:
            message_bus_instance.invoke(
                SupprimerDocumentCommand(
                    uuid_parcours_doctoral=self.parcours_doctoral_uuid,
                    identifiant=str(self.kwargs['document_identifier']),
                )
            )
        except BusinessException as exception:
            self.message_on_failure = exception.message
            response = self.form_invalid(form)
            response.status_code = 400
            return response

        return super().form_valid(form)
