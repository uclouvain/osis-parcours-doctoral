# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.urls import reverse
from django.views.generic import FormView

from parcours_doctoral.ddd.epreuve_confirmation.commands import (
    SoumettreAvisProlongationCommand,
)
from parcours_doctoral.forms.extension_request import ExtensionRequestForm
from parcours_doctoral.views.mixins import LastConfirmationMixin
from admission.views.mixins.business_exceptions_form_view_mixin import BusinessExceptionFormViewMixin
from infrastructure.messages_bus import message_bus_instance

__all__ = [
    "ExtensionRequestFormView",
]


class ExtensionRequestFormView(
    LastConfirmationMixin,
    BusinessExceptionFormViewMixin,
    FormView,
):
    template_name = 'parcours_doctoral/forms/extension_request.html'
    permission_required = 'admission.change_admission_confirmation_extension'
    form_class = ExtensionRequestForm

    def get_initial(self):
        return (
            {
                'avis_cdd': self.last_confirmation_paper.demande_prolongation.avis_cdd,
            }
            if self.last_confirmation_paper.demande_prolongation
            else {}
        )

    def call_command(self, form):
        message_bus_instance.invoke(
            SoumettreAvisProlongationCommand(
                uuid=self.last_confirmation_paper.uuid,
                **form.cleaned_data,
            )
        )

    def get_success_url(self):
        return reverse('admission:doctorate:extension-request', args=[self.admission_uuid])
