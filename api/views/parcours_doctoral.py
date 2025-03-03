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
from typing import List

from django.db.models import Prefetch
from osis_signature.models import Actor
from rest_framework import mixins
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response

from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin
from parcours_doctoral.api import serializers
from parcours_doctoral.api.permissions import DoctorateAPIPermissionRequiredMixin
from parcours_doctoral.api.schema import ResponseSpecificSchema
from parcours_doctoral.ddd.commands import (
    ListerParcoursDoctorauxDoctorantQuery,
    ListerParcoursDoctorauxSupervisesQuery,
    RecupererParcoursDoctoralQuery,
)
from parcours_doctoral.ddd.dtos import ParcoursDoctoralRechercheEtudiantDTO
from parcours_doctoral.models import ParcoursDoctoral

__all__ = [
    "DoctorateAPIView",
    "DoctorateListView",
    "SupervisedDoctorateListView",
]


class DoctorateSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'GET': serializers.ParcoursDoctoralDTOSerializer,
    }


class DoctorateAPIView(
    DoctorateAPIPermissionRequiredMixin,
    mixins.RetrieveModelMixin,
    GenericAPIView,
):
    name = "doctorate"
    pagination_class = None
    filter_backends = []
    schema = DoctorateSchema()
    permission_mapping = {
        'GET': 'parcours_doctoral.view_parcours_doctoral',
    }

    def get(self, request, *args, **kwargs):
        """Get the parcours doctoral"""
        doctorate_dto = message_bus_instance.invoke(
            RecupererParcoursDoctoralQuery(parcours_doctoral_uuid=self.doctorate_uuid),
        )

        # Add a _perm_obj to the instance to optimize permission check performance
        doctorate_permission_obj = ParcoursDoctoral.objects.select_related(
            'student',
            'admission',
            'training__management_entity__doctorate_config',
        ).get(uuid=doctorate_dto.uuid)

        doctorate_dto._perm_obj = doctorate_permission_obj

        serializer = serializers.ParcoursDoctoralDTOSerializer(
            instance=doctorate_dto,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)


class BaseListView(APIPermissionRequiredMixin, ListAPIView):
    name = "list"
    pagination_class = None
    filter_backends = []
    serializer_class = serializers.ParcoursDoctoralRechercheDTOSerializer

    def doctorate_list(self, request) -> List[ParcoursDoctoralRechercheEtudiantDTO]:
        """List the PhDs of the logged-in user."""
        raise NotImplementedError

    def permission_object_qs(self, doctorate_list: List[ParcoursDoctoralRechercheEtudiantDTO]):
        return ParcoursDoctoral.objects.select_related(
            'student',
            'admission',
            'training__management_entity__doctorate_config',
        ).filter(uuid__in=[doctorate.uuid for doctorate in doctorate_list])

    def list(self, request, **kwargs):
        doctorate_list = self.doctorate_list(request)

        # Add a _perm_obj to each instance to optimize permission check performance
        permission_object_qs = {
            str(doctorate.uuid): doctorate for doctorate in self.permission_object_qs(doctorate_list=doctorate_list)
        }

        for doctorate in doctorate_list:
            doctorate._perm_obj = permission_object_qs[doctorate.uuid]

        serializer = serializers.ParcoursDoctoralRechercheDTOSerializer(
            instance=doctorate_list,
            context=self.get_serializer_context(),
            many=True,
        )

        return Response(serializer.data)


class DoctorateListSchema(ResponseSpecificSchema):
    operation_id_base = '_doctorates'
    serializer_mapping = {
        'GET': serializers.ParcoursDoctoralRechercheDTOSerializer,
    }


class DoctorateListView(BaseListView):
    name = "list"
    schema = DoctorateListSchema()
    permission_mapping = {
        'GET': 'parcours_doctoral.view_list',
    }

    def doctorate_list(self, request):
        """List the PhDs of the logged-in user."""
        return message_bus_instance.invoke(
            ListerParcoursDoctorauxDoctorantQuery(matricule_doctorant=request.user.person.global_id),
        )


class SupervisedDoctorateListSchema(DoctorateListSchema):
    operation_id_base = '_supervised_doctorates'


class SupervisedDoctorateListView(BaseListView):
    name = "supervised_list"
    schema = SupervisedDoctorateListSchema()
    permission_mapping = {
        'GET': 'parcours_doctoral.view_supervised_list',
    }

    def permission_object_qs(self, doctorate_list):
        qs = super().permission_object_qs(doctorate_list)
        return qs.select_related('supervision_group').prefetch_related(
            Prefetch(
                'supervision_group__actors',
                Actor.objects.select_related('parcoursdoctoralsupervisionactor').all(),
            )
        )

    def doctorate_list(self, request):
        """List the supervised PhDs of the logged-in user."""
        return message_bus_instance.invoke(
            ListerParcoursDoctorauxSupervisesQuery(matricule_membre=request.user.person.global_id),
        )
