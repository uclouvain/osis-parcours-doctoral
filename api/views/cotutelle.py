# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.api import serializers
from parcours_doctoral.api.permissions import DoctorateAPIPermissionRequiredMixin
from parcours_doctoral.api.schema import ResponseSpecificSchema
from parcours_doctoral.ddd.commands import ModifierCotutelleCommand

__all__ = [
    "CotutelleAPIView",
]


class CotutelleSchema(ResponseSpecificSchema):
    operation_id_base = '_cotutelle'
    serializer_mapping = {
        'PUT': (serializers.ModifierCotutelleCommandSerializer, serializers.ParcoursDoctoralIdentityDTOSerializer),
    }


class CotutelleAPIView(
    DoctorateAPIPermissionRequiredMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericAPIView,
):
    name = "cotutelle"
    schema = CotutelleSchema()
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.view_cotutelle',
        'PUT': 'parcours_doctoral.change_cotutelle',
    }

    def get(self, request, *args, **kwargs):
        """
        This method is only used to check the permission.
        We have to return some data as the schema expects a 200 status and the deserializer expects some data.
        """
        return Response(data={})

    def put(self, request, *args, **kwargs):
        """Set the cotutelle of the PhD."""
        serializer = serializers.ModifierCotutelleCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = message_bus_instance.invoke(
            ModifierCotutelleCommand(
                uuid_proposition=self.doctorate_uuid,
                matricule_auteur=self.request.user.person.global_id,
                **serializer.data,
            )
        )
        serializer = serializers.ParcoursDoctoralIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)
