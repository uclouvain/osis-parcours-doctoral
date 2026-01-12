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

from django.shortcuts import resolve_url
from django.views.generic import FormView

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.recevabilite.commands import ModifierRecevabiliteCommand
from parcours_doctoral.forms.admissibility import AdmissibilityForm
from parcours_doctoral.views.details.admissibility import AdmissibilityCommonViewMixin
from parcours_doctoral.views.mixins import (
    BusinessExceptionFormViewMixin,
    ParcoursDoctoralFormMixin,
)

__all__ = [
    "AdmissibilityFormView",
]


class AdmissibilityFormView(
    AdmissibilityCommonViewMixin,
    ParcoursDoctoralFormMixin,
    BusinessExceptionFormViewMixin,
    FormView,
):
    template_name = 'parcours_doctoral/forms/admissibility.html'
    permission_required = 'parcours_doctoral.change_admissibility'
    form_class = AdmissibilityForm

    def get_initial(self):
        initial_data: dict = {'titre_these': self.parcours_doctoral_dto.titre_these_propose}

        current_admissibility = self.current_admissibility

        if current_admissibility:
            initial_data['date_envoi_manuscrit'] = current_admissibility.date_envoi_manuscrit
            initial_data['date_decision'] = current_admissibility.date_decision
            initial_data['proces_verbal'] = current_admissibility.proces_verbal
            initial_data['avis_jury'] = current_admissibility.avis_jury

        return initial_data

    def call_command(self, form):
        message_bus_instance.invoke(
            ModifierRecevabiliteCommand(
                parcours_doctoral_uuid=self.parcours_doctoral_uuid,
                matricule_auteur=self.request.user.person.global_id,
                titre_these=form.cleaned_data['titre_these'],
                date_envoi_manuscrit=form.cleaned_data['date_envoi_manuscrit'],
                date_decision=form.cleaned_data['date_decision'],
                proces_verbal=form.cleaned_data['proces_verbal'],
                avis_jury=form.cleaned_data['avis_jury'],
            )
        )

    def get_success_url(self):
        return resolve_url('parcours_doctoral:admissibility', uuid=self.parcours_doctoral_uuid)
