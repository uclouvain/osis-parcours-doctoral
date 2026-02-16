# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.conf import settings
from django.db.models import Exists, F, OuterRef, Q
from rest_framework.filters import BaseFilterBackend
from rest_framework.generics import ListAPIView

from base.auth.roles.tutor import Tutor
from base.models.person import Person
from base.models.student import Student
from parcours_doctoral.api import serializers

__all__ = [
    "AutocompleteTutorView",
    "AutocompletePersonView",
]


class PersonSearchingBackend(BaseFilterBackend):
    searching_param = 'search'

    def filter_queryset(self, request, queryset, view):
        search_term = request.GET.get(self.searching_param, '')
        return queryset.filter(
            *[
                Q(first_name__icontains=term) | Q(last_name__icontains=term) | Q(global_id__icontains=search_term)
                for term in search_term.split()
            ],
        )

    def get_schema_operation_parameters(self, view):  # pragma: no cover
        return [
            {
                'name': self.searching_param,
                'required': True,
                'in': 'query',
                'description': "The term to search the persons on (first or last name, or global id)",
                'schema': {
                    'type': 'string',
                },
            },
        ]


class AutocompleteTutorView(ListAPIView):
    """Autocomplete tutors"""

    name = "tutor"
    filter_backends = [PersonSearchingBackend]
    serializer_class = serializers.TutorSerializer
    queryset = (
        Tutor.objects.annotate(
            first_name=F("person__first_name"),
            last_name=F("person__last_name"),
            global_id=F("person__global_id"),
        )
        .filter(
            # Keep only employees with internal account and email address
            person__employee=True,
            person__global_id__startswith='0',
            person__email__endswith=settings.INTERNAL_EMAIL_SUFFIX,
        )
        .distinct('global_id')
        .select_related("person")
    )


class AutocompletePersonView(ListAPIView):
    """Autocomplete person"""

    name = "person"
    filter_backends = [PersonSearchingBackend]
    serializer_class = serializers.PersonSerializer
    queryset = (
        Person.objects.exclude(
            # Remove unexistent users
            Q(first_name='') | Q(last_name='')
        )
        .alias(
            is_student_and_not_tutor=Exists(Student.objects.filter(person=OuterRef('pk'), person__tutor__isnull=True)),
        )
        .filter(
            # Keep only employees with internal account and email address
            employee=True,
            global_id__startswith='0',
            email__endswith=settings.INTERNAL_EMAIL_SUFFIX,
            # Remove students who aren't tutors
            is_student_and_not_tutor=False,
        )
        .order_by('first_name', 'last_name')
    )
