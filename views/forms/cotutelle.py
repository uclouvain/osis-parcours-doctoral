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
import attr
from django.shortcuts import resolve_url
from django.views.generic import FormView

from admission.views.mixins.business_exceptions_form_view_mixin import (
    BusinessExceptionFormViewMixin,
)
from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.commands import ModifierCotutelleCommand
from parcours_doctoral.forms.cotutelle import CotutelleForm
from parcours_doctoral.views.mixins import ParcoursDoctoralFormMixin

__all__ = [
    'CotutelleFormView',
]


class CotutelleFormView(
    ParcoursDoctoralFormMixin,
    BusinessExceptionFormViewMixin,
    FormView,
):
    template_name = 'parcours_doctoral/forms/cotutelle.html'
    permission_required = 'parcours_doctoral.change_cotutelle'
    form_class = CotutelleForm

    def get_success_url(self):
        return resolve_url('parcours_doctoral:cotutelle', uuid=self.parcours_doctoral_uuid)

    def get_initial(self):
        initial = attr.asdict(self.parcours_doctoral_dto.cotutelle)

        if initial['cotutelle'] is not None:
            initial['cotutelle'] = 'YES' if initial['cotutelle'] else 'NO'

            if initial['institution_fwb'] is not None:
                initial['institution_fwb'] = 'true' if initial['institution_fwb'] else 'false'

        return initial

    def prepare_data(self, data: dict):
        del data['cotutelle']
        del data['autre_institution']
        return data

    def call_command(self, form):
        message_bus_instance.invoke(
            ModifierCotutelleCommand(
                uuid_proposition=self.parcours_doctoral_uuid,
                matricule_auteur=self.request.user.person.global_id,
                **self.prepare_data(form.cleaned_data),
            )
        )
