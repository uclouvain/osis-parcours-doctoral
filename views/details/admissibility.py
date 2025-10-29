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

from django.utils.functional import cached_property
from django.views.generic import TemplateView

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.recevabilite.commands import RecupererRecevabilitesQuery
from parcours_doctoral.ddd.recevabilite.dtos import RecevabiliteDTO
from parcours_doctoral.views.mixins import ParcoursDoctoralViewMixin

__all__ = [
    "AdmissibilityDetailView",
]


class AdmissibilityCommonViewMixin:
    @cached_property
    def admissibilities(self) -> list[RecevabiliteDTO]:
        return message_bus_instance.invoke(
            RecupererRecevabilitesQuery(parcours_doctoral_uuid=self.parcours_doctoral_uuid)
        )

    @cached_property
    def current_admissibility(self) -> RecevabiliteDTO | None:
        return next((admissibility for admissibility in self.admissibilities if admissibility.est_active), None)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['all_admissibilities'] = self.admissibilities
        context['current_admissibility'] = self.current_admissibility
        context['supervisors'] = [member for member in self.jury.membres if member.est_promoteur]

        return context


class AdmissibilityDetailView(AdmissibilityCommonViewMixin, ParcoursDoctoralViewMixin, TemplateView):
    template_name = 'parcours_doctoral/details/admissibility.html'
    permission_required = 'parcours_doctoral.view_admissibility'
