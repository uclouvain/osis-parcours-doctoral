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
from django.utils.functional import cached_property
from django.views.generic import TemplateView

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.autorisation_diffusion_these.commands import (
    RecupererAutorisationDiffusionTheseQuery,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.dtos.autorisation_diffusion_these import (
    AutorisationDiffusionTheseDTO,
)
from parcours_doctoral.views.mixins import ParcoursDoctoralViewMixin

__all__ = [
    'ManuscriptValidationDetailView',
]

__namespace__ = False


class ManuscriptValidationCommonViewMixin(ParcoursDoctoralViewMixin):
    @cached_property
    def authorization_distribution(self) -> AutorisationDiffusionTheseDTO:
        return message_bus_instance.invoke(
            RecupererAutorisationDiffusionTheseQuery(
                uuid_parcours_doctoral=self.parcours_doctoral_uuid,
            )
        )

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['authorization_distribution'] = self.authorization_distribution
        context_data['signatories'] = {
            signatory.role: signatory for signatory in self.authorization_distribution.signataires
        }
        return context_data

    def get_success_url(self):
        return resolve_url('parcours_doctoral:manuscript-validation', uuid=self.parcours_doctoral_uuid)


class ManuscriptValidationDetailView(ManuscriptValidationCommonViewMixin, TemplateView):
    urlpatterns = 'manuscript-validation'
    template_name = 'parcours_doctoral/details/manuscript_validation.html'
    permission_required = 'parcours_doctoral.view_manuscript_validation'
