# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
from rest_framework.permissions import BasePermission

from osis_role.contrib.views import APIPermissionRequiredMixin
from parcours_doctoral.models import ParcoursDoctoral
from parcours_doctoral.utils.cache import get_cached_parcours_doctoral_perm_obj


class IsSupervisionMember(BasePermission):
    def has_permission(self, request, view):
        # User is among supervision actors
        return ParcoursDoctoral.objects.filter(
            supervision_group__actors__person=request.user.person,
        ).exists()


class IsPhDStudent(BasePermission):
    def has_permission(self, request, view):
        # User is among PhD students
        return ParcoursDoctoral.objects.filter(
            student=request.user.person,
        ).exists()


class DoctorateAPIPermissionRequiredMixin(APIPermissionRequiredMixin):
    @property
    def doctorate_uuid(self):
        return self.kwargs['uuid']

    def get_permission_object(self):
        return get_cached_parcours_doctoral_perm_obj(self.doctorate_uuid)
