# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.db.models import Case, F, Q, When
from django.db.models.functions import Coalesce

from base.models.person import Person
from parcours_doctoral.auth.roles.student import Student
from parcours_doctoral.models import JuryMember, ParcoursDoctoralSupervisionActor

__all__ = [
    'JuryMembersAutocomplete',
    'PersonsAutocomplete',
    'SupervisionActorsAutocomplete',
    'StudentsAutocomplete',
    'AuditorAutocomplete',
]

__namespace__ = False


class PersonsAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    url_patterns = 'persons'

    def get_results(self, context):
        return [
            {
                'id': person.get('global_id'),
                'text': ', '.join([person.get('last_name'), person.get('first_name')]),
            }
            for person in context['object_list']
        ]

    def get_queryset(self):
        q = self.request.GET.get('q', '')

        return (
            Person.objects.annotate(
                name=SearchVector(
                    'first_name',
                    'last_name',
                ),
            )
            .filter(Q(name=q) | Q(global_id__contains=q))
            .order_by('last_name', 'first_name')
            .values(
                'first_name',
                'last_name',
                'global_id',
            )
            .distinct()
            if q
            else []
        )


class StudentsAutocomplete(PersonsAutocomplete):
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
            .filter(Q(name=q) | Q(person__global_id__contains=q) | Q(person__student__registration_id__icontains=q))
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


class SupervisionActorsAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    urlpatterns = 'supervision-actors'

    def get_results(self, context):
        return [
            {
                'id': actor.get('uuid'),
                'text': ', '.join([actor.get('current_last_name'), actor.get('current_first_name')]),
            }
            for actor in context['object_list']
        ]

    def get_queryset(self):
        if not self.q:
            return []

        actor_type = self.forwarded.get('actor_type')

        qs = (
            ParcoursDoctoralSupervisionActor.objects.annotate(
                current_first_name=Coalesce(
                    F('person__first_name'),
                    F('first_name'),
                ),
                current_last_name=Coalesce(
                    F('person__last_name'),
                    F('last_name'),
                ),
                name=SearchVector(
                    'current_first_name',
                    'current_last_name',
                ),
            )
            .filter(Q(name=self.q) | Q(person__global_id__contains=self.q))
            .order_by('current_last_name', 'current_first_name')
        )

        if actor_type:
            qs = qs.filter(type=actor_type)

        return qs.values(
            'uuid',
            'current_first_name',
            'current_last_name',
        )


class JuryMembersAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    urlpatterns = 'jury-members'

    def get_results(self, context):
        return [
            {
                'id': actor.get('uuid'),
                'text': ', '.join([actor.get('current_last_name'), actor.get('current_first_name')]),
            }
            for actor in context['object_list']
        ]

    def get_queryset(self):
        if not self.q:
            return []

        role = self.forwarded.get('role')

        qs = (
            JuryMember.objects.annotate(
                current_first_name=Coalesce(
                    F('person__first_name'),
                    F('promoter__person__first_name'),
                    F('promoter__first_name'),
                    F('first_name'),
                ),
                current_last_name=Coalesce(
                    F('person__last_name'),
                    F('promoter__person__last_name'),
                    F('promoter__last_name'),
                    F('last_name'),
                ),
                current_global_id=Coalesce(
                    F('person__global_id'),
                    F('promoter__person__global_id'),
                ),
                name=SearchVector(
                    'current_first_name',
                    'current_last_name',
                ),
            )
            .filter(Q(name=self.q) | Q(current_global_id__contains=self.q))
            .order_by('current_last_name', 'current_first_name')
        )

        if role:
            qs = qs.filter(role=role)

        return qs.values(
            'uuid',
            'current_first_name',
            'current_last_name',
        )


class AuditorAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    urlpatterns = 'auditors'

    def get_queryset(self):
        q = self.request.GET.get('q', '')

        return (
            Person.objects.annotate(
                name=SearchVector(
                    'first_name',
                    'last_name',
                ),
            )
            .filter(Q(name=q) | Q(global_id__contains=q))
            .exclude(student__isnull=False)
            .order_by('last_name', 'first_name')
            .distinct()
        )
