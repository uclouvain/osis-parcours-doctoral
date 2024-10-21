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
from dal import autocomplete
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.search import SearchVector
from django.db.models import Exists, F, OuterRef, Q

__all__ = [
    'StudentsAutocomplete',
]

__namespace__ = False

from parcours_doctoral.auth.roles.student import Student


class PersonsAutocomplete(LoginRequiredMixin):
    def get_results(self, context):
        return [
            {
                'id': person.get('global_id'),
                'text': ', '.join([person.get('last_name'), person.get('first_name')]),
            }
            for person in context['object_list']
        ]


class StudentsAutocomplete(PersonsAutocomplete, autocomplete.Select2QuerySetView):
    urlpatterns = 'students'

    def get_queryset(self):
        q = self.request.GET.get('q', '')

        return (
            Student.objects.annotate(
                name=SearchVector(
                    'person__first_name',
                    'person__last_name',
                ),
            )
            .filter(
                Q(name=q)
                | Q(person__email__icontains=q)
                | Q(person__private_email__icontains=q)
                | Q(person__student__registration_id__icontains=q)
            )
            .order_by('person__last_name', 'person__first_name')
            .values(
                first_name=F('person__first_name'),
                last_name=F('person__last_name'),
                global_id=F('person__global_id'),
            )
            .distinct()
            if q
            else []
        )
