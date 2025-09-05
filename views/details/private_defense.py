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

from typing import List

from django.views.generic import TemplateView

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.commands import GetGroupeDeSupervisionQuery
from parcours_doctoral.ddd.defense_privee.commands import RecupererDefensesPriveesQuery
from parcours_doctoral.ddd.defense_privee.dtos import DefensePriveeDTO
from parcours_doctoral.views.mixins import ParcoursDoctoralViewMixin

__all__ = [
    "PrivateDefenseDetailView",
]


class PrivateDefenseDetailView(ParcoursDoctoralViewMixin, TemplateView):
    template_name = 'parcours_doctoral/details/private_defense.html'
    permission_required = 'parcours_doctoral.view_private_defense'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        all_private_defenses: List[DefensePriveeDTO] = message_bus_instance.invoke(
            RecupererDefensesPriveesQuery(parcours_doctoral_uuid=self.parcours_doctoral_uuid)
        )

        if all_private_defenses:
            context['current_private_defense'] = all_private_defenses.pop(0)

        context['previous_private_defenses'] = all_private_defenses

        context['supervision'] = message_bus_instance.invoke(
            GetGroupeDeSupervisionQuery(uuid_parcours_doctoral=self.parcours_doctoral_uuid)
        )

        return context
