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

from django.core.cache import cache
from django.shortcuts import get_object_or_404

from parcours_doctoral.models.parcours_doctoral import ParcoursDoctoral


def get_cached_parcours_doctoral_perm_obj(parcours_doctoral_uuid):
    qs = ParcoursDoctoral.objects.select_related(
        'student',
        'admission',
        'training__academic_year',
        'thesis_distribution_authorization',
    )
    return cache.get_or_set(
        'parcours_doctoral_permission_{}'.format(parcours_doctoral_uuid),
        lambda: get_object_or_404(qs, uuid=parcours_doctoral_uuid),
    )
