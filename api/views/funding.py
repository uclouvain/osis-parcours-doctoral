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
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.api import serializers
from parcours_doctoral.api.permissions import DoctorateAPIPermissionRequiredMixin
from parcours_doctoral.ddd.commands import ModifierFinancementCommand

__all__ = [
    "FundingApiView",
]


class FundingApiView(
    DoctorateAPIPermissionRequiredMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericAPIView,
):
    name = "funding"
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.api_view_funding',
        'PUT': 'parcours_doctoral.api_change_funding',
    }

    @extend_schema(
        request=None,
        responses=None,
        operation_id='retrieve_funding',
    )
    def get(self, request, *args, **kwargs):
        """
        This method is only used to check the permission.
        We have to return some data as the schema expects a 200 status and the deserializer expects some data.
        """
        return Response(data={})

    @extend_schema(
        request=serializers.ModifierFinancementCommandSerializer,
        responses=serializers.ParcoursDoctoralIdentityDTOSerializer,
        operation_id='update_funding',
    )
    def put(self, request, *args, **kwargs):
        """Edit the project"""
        serializer = serializers.ModifierFinancementCommandSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        result = message_bus_instance.invoke(
            ModifierFinancementCommand(
                uuid=self.doctorate_uuid,
                matricule_auteur=self.request.user.person.global_id,
                **serializer.data,
            )
        )

        serializer = serializers.ParcoursDoctoralIdentityDTOSerializer(instance=result)

        return Response(serializer.data, status=status.HTTP_200_OK)
