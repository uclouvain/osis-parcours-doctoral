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

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.commands import ModifierFinancementCommand
from parcours_doctoral.ddd.domain.validator.exceptions import (
    ContratTravailInconsistantException,
)
from parcours_doctoral.forms.funding import FundingForm
from parcours_doctoral.views.mixins import (
    BusinessExceptionFormViewMixin,
    ParcoursDoctoralFormMixin,
)

__all__ = [
    "FundingFormView",
]


class FundingFormView(
    ParcoursDoctoralFormMixin,
    BusinessExceptionFormViewMixin,
    FormView,
):
    template_name = 'parcours_doctoral/forms/funding.html'
    permission_required = 'parcours_doctoral.change_funding'
    form_class = FundingForm
    error_mapping = {
        ContratTravailInconsistantException: 'type_contrat_travail',
    }

    def get_success_url(self):
        return resolve_url('parcours_doctoral:funding', uuid=self.parcours_doctoral_uuid)

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['admission_type'] = self.parcours_doctoral_dto.type_admission
        return form_kwargs

    def get_initial(self):
        initial = attr.asdict(self.parcours_doctoral_dto.financement)

        if self.parcours_doctoral_dto.financement.bourse_recherche:
            initial['bourse_recherche'] = self.parcours_doctoral_dto.financement.bourse_recherche.uuid

        return initial

    def call_command(self, form):
        message_bus_instance.invoke(
            ModifierFinancementCommand(
                uuid=self.parcours_doctoral_uuid,
                matricule_auteur=self.request.user.person.global_id,
                **form.cleaned_data,
            )
        )
