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
from django.views.generic import RedirectView

from osis_role.contrib.views import PermissionRequiredMixin

__all__ = ["SupervisionDetailView"]

from parcours_doctoral.utils.cache import get_cached_parcours_doctoral_perm_obj


class SupervisionDetailView(PermissionRequiredMixin, RedirectView):
    permission_required = 'parcours_doctoral.view_supervision'

    def get_permission_object(self):
        return get_cached_parcours_doctoral_perm_obj(self.kwargs.get('uuid'))

    def get_redirect_url(self, *args, **kwargs):
        return resolve_url('parcours_doctoral:update:supervision', uuid=self.kwargs['uuid'])
