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

from django.views.generic import FormView

from base.utils.htmx import HtmxPermissionRequiredMixin
from infrastructure.messages_bus import message_bus_instance
from osis_common.utils.htmx import HtmxMixin
from parcours_doctoral.ddd.read_view.queries import (
    RecupererInformationsTableauBordQuery,
)
from parcours_doctoral.forms.dashboard import DashboardForm

__all__ = [
    'DashboardView',
]


class DashboardView(HtmxPermissionRequiredMixin, HtmxMixin, FormView):
    permission_required = 'parcours_doctoral.view_parcours_doctoral'
    template_name = 'parcours_doctoral/dashboard.html'
    htmx_template_name = 'parcours_doctoral/dashboard_htmx.html'
    form_class = DashboardForm

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['user'] = self.request.user
        return form_kwargs

    def form_valid(self, form):
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        form = context_data['form']

        if not form.is_bound or form.is_valid():
            cmd_params = getattr(form, 'cleaned_data', {})

            if not cmd_params.get('cdds'):
                cmd_params['cdds'] = form.cdd_acronyms

            context_data['dashboard'] = message_bus_instance.invoke(RecupererInformationsTableauBordQuery(**cmd_params))

        return context_data
