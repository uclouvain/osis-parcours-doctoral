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

from django.views.generic import RedirectView

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.commands import GetGroupeDeSupervisionQuery
from parcours_doctoral.exports.confirmation_canvas import (
    parcours_doctoral_pdf_confirmation_canvas,
)
from parcours_doctoral.models import Activity
from parcours_doctoral.views.mixins import LastConfirmationMixin

__all__ = [
    "ConfirmationCanvasExportView",
]


class ConfirmationCanvasExportView(LastConfirmationMixin, RedirectView):
    permission_required = 'parcours_doctoral.view_confirmation'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data()
        context_data['supervision_group'] = message_bus_instance.invoke(
            GetGroupeDeSupervisionQuery(uuid_parcours_doctoral=self.parcours_doctoral_uuid),
        )
        context_data['supervision_people_nb'] = (
            # total actor count
            len(context_data['supervision_group'].signatures_promoteurs)
            + len(context_data['supervision_group'].signatures_membres_CA)
        )
        context_data['doctoral_training_ects_nb'] = Activity.objects.get_doctoral_training_credits_number(
            parcours_doctoral_uuid=self.parcours_doctoral_uuid,
        )

        context_data['has_additional_training'] = Activity.objects.has_complementary_training(
            parcours_doctoral_uuid=self.parcours_doctoral_uuid,
        )

        return context_data

    def get(self, request, *args, **kwargs):
        from osis_document.api.utils import get_remote_token
        from osis_document.utils import get_file_url

        file_uuid = parcours_doctoral_pdf_confirmation_canvas(
            parcours_doctoral=self.parcours_doctoral,
            language=self.parcours_doctoral.student.language,
            context=self.get_context_data(),
        )
        reading_token = get_remote_token(file_uuid, for_modified_upload=True)

        self.url = get_file_url(reading_token)

        return super().get(request, *args, **kwargs)
