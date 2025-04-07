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
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.epreuve_confirmation.commands import (
    SoumettreReportDeDateParCDDCommand,
)
from parcours_doctoral.forms.extension_request import ExtensionRequestForm
from parcours_doctoral.views.mixins import (
    BusinessExceptionFormViewMixin,
    LastConfirmationMixin,
)

__all__ = [
    "ExtensionRequestFormView",
]


class ExtensionRequestFormView(
    LastConfirmationMixin,
    BusinessExceptionFormViewMixin,
    FormView,
):
    template_name = 'parcours_doctoral/forms/extension_request.html'
    permission_required = 'parcours_doctoral.change_confirmation_extension'
    form_class = ExtensionRequestForm

    def dispatch(self, request, *args, **kwargs):
        if (
            self.parcours_doctoral.status != ChoixStatutParcoursDoctoral.ADMIS.name
            and self.parcours_doctoral.status != ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name
        ):
            return redirect("parcours_doctoral:extension-request", uuid=self.parcours_doctoral.uuid)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        return (
            {
                'nouvelle_echeance': self.last_confirmation_paper.demande_prolongation.nouvelle_echeance,
                'justification_succincte': self.last_confirmation_paper.demande_prolongation.justification_succincte,
                'lettre_justification': self.last_confirmation_paper.demande_prolongation.lettre_justification,
            }
            if self.last_confirmation_paper.demande_prolongation
            else {}
        )

    def call_command(self, form):
        message_bus_instance.invoke(
            SoumettreReportDeDateParCDDCommand(
                uuid=self.last_confirmation_paper.uuid,
                **form.cleaned_data,
            )
        )

    def get_success_url(self):
        return reverse('parcours_doctoral:extension-request', args=[self.parcours_doctoral_uuid])
