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
from parcours_doctoral.ddd.defense_privee.commands import ModifierDefensePriveeCommand
from parcours_doctoral.forms.private_defense import PrivateDefenseForm
from parcours_doctoral.views.details.private_defense import (
    PrivateDefenseCommonViewMixin,
)
from parcours_doctoral.views.mixins import (
    BusinessExceptionFormViewMixin,
    ParcoursDoctoralFormMixin,
)

__all__ = [
    "PrivateDefenseFormView",
]


class PrivateDefenseFormView(
    PrivateDefenseCommonViewMixin,
    ParcoursDoctoralFormMixin,
    BusinessExceptionFormViewMixin,
    FormView,
):
    template_name = 'parcours_doctoral/forms/private_defense.html'
    permission_required = 'parcours_doctoral.change_private_defense'
    form_class = PrivateDefenseForm

    def get_initial(self):
        initial_data: dict = {
            'titre_these': self.parcours_doctoral.thesis_proposed_title,
        }

        current_private_defense = self.current_private_defense

        if current_private_defense:
            initial_data['date_heure_defense_privee'] = current_private_defense.date_heure
            initial_data['lieu_defense_privee'] = current_private_defense.lieu
            initial_data['date_envoi_manuscrit'] = current_private_defense.date_envoi_manuscrit
            initial_data['proces_verbal_defense_privee'] = current_private_defense.proces_verbal

        return initial_data

    def call_command(self, form):
        message_bus_instance.invoke(
            ModifierDefensePriveeCommand(
                uuid=self.current_private_defense.uuid,
                matricule_auteur=self.request.user.person.global_id,
                titre_these=form.cleaned_data['titre_these'],
                date_heure=form.cleaned_data['date_heure_defense_privee'],
                lieu=form.cleaned_data['lieu_defense_privee'],
                date_envoi_manuscrit=form.cleaned_data['date_envoi_manuscrit'],
                proces_verbal=form.cleaned_data['proces_verbal_defense_privee'],
            )
        )

    def get_success_url(self):
        return resolve_url('parcours_doctoral:private-defense', uuid=self.parcours_doctoral_uuid)
