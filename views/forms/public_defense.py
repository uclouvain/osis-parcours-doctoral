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
from parcours_doctoral.ddd.soutenance_publique.commands import ModifierSoutenancePubliqueCommand
from parcours_doctoral.forms.public_defense import PublicDefenseForm
from parcours_doctoral.views.mixins import (
    BusinessExceptionFormViewMixin,
    ParcoursDoctoralFormMixin,
)

__all__ = [
    "PublicDefenseFormView",
]


class PublicDefenseFormView(
    ParcoursDoctoralFormMixin,
    BusinessExceptionFormViewMixin,
    FormView,
):
    template_name = 'parcours_doctoral/forms/public_defense.html'
    permission_required = 'parcours_doctoral.change_public_defense'
    form_class = PublicDefenseForm

    def get_initial(self):
        return {
            'langue': self.parcours_doctoral_dto.langue_soutenance_publique,
            'date_heure': self.parcours_doctoral_dto.date_heure_soutenance_publique,
            'lieu': self.parcours_doctoral_dto.lieu_soutenance_publique,
            'local_deliberation': self.parcours_doctoral_dto.local_deliberation,
            'informations_complementaires': self.parcours_doctoral_dto.informations_complementaires_soutenance_publique,
            'resume_annonce': self.parcours_doctoral_dto.resume_annonce,
            'photo_annonce': self.parcours_doctoral_dto.photo_annonce,
            'proces_verbal': self.parcours_doctoral_dto.proces_verbal_soutenance_publique,
            'date_retrait_diplome': self.parcours_doctoral_dto.date_retrait_diplome,
        }

    def call_command(self, form):
        message_bus_instance.invoke(
            ModifierSoutenancePubliqueCommand(
                uuid_parcours_doctoral=self.parcours_doctoral_uuid,
                matricule_auteur=self.request.user.person.global_id,
                **form.cleaned_data,
            )
        )

    def get_success_url(self):
        return resolve_url('parcours_doctoral:public-defense', uuid=self.parcours_doctoral_uuid)
