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
from parcours_doctoral.api.permissions import DoctorateAPIPermissionRequiredMixin
from parcours_doctoral.api.schema import ResponseSpecificSchema
from parcours_doctoral.api.serializers import (
    AjouterMembreCommandSerializer,
    JuryDTOSerializer,
    JuryIdentityDTOSerializer,
    MembreJuryDTOSerializer,
    MembreJuryIdentityDTOSerializer,
    ModifierJuryCommandSerializer,
    ModifierMembreCommandSerializer,
    ModifierRoleMembreCommandSerializer,
)
from parcours_doctoral.ddd.jury.commands import (
    AjouterMembreCommand,
    ModifierJuryCommand,
    ModifierMembreCommand,
    ModifierRoleMembreCommand,
    RecupererJuryMembreQuery,
    RecupererJuryQuery,
    RetirerMembreCommand,
)

__all__ = [
    "JuryPreparationAPIView",
    "JuryMembersListAPIView",
    "JuryMemberDetailAPIView",
]


class JuryPreparationSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'GET': JuryDTOSerializer,
        'POST': (ModifierJuryCommandSerializer, JuryIdentityDTOSerializer),
    }

    method_mapping = {
        'get': 'retrieve',
        'post': 'update',
    }

    operation_id_base = '_jury_preparation'


class JuryPreparationAPIView(
    DoctorateAPIPermissionRequiredMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericAPIView,
):
    name = "jury-preparation"
    schema = JuryPreparationSchema()
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.view_jury',
        'POST': 'parcours_doctoral.change_jury',
    }

    def get(self, request, *args, **kwargs):
        """Get the Jury of a doctorate"""
        jury = message_bus_instance.invoke(RecupererJuryQuery(uuid_jury=self.doctorate_uuid))
        serializer = JuryDTOSerializer(instance=jury)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """Update the jury preparation information"""
        serializer = ModifierJuryCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = message_bus_instance.invoke(
            ModifierJuryCommand(
                uuid_parcours_doctoral=str(self.doctorate_uuid),
                **serializer.data,
            )
        )
        serializer = JuryIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)


class JuryMembersListSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'GET': MembreJuryDTOSerializer,
        'POST': (AjouterMembreCommandSerializer, MembreJuryIdentityDTOSerializer),
    }

    method_mapping = {
        'get': 'list',
        'post': 'create',
    }

    operation_id_base = '_jury_members'


class JuryMembersListAPIView(
    DoctorateAPIPermissionRequiredMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericAPIView,
):
    name = "jury-members-list"
    schema = JuryMembersListSchema()
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.view_jury',
        'POST': 'parcours_doctoral.change_jury',
    }

    def get(self, request, *args, **kwargs):
        """Get the members of a jury"""
        jury = message_bus_instance.invoke(RecupererJuryQuery(uuid_jury=self.doctorate_uuid))
        serializer = MembreJuryDTOSerializer(instance=jury.membres, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """Add a new member to the jury"""
        serializer = AjouterMembreCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = message_bus_instance.invoke(
            AjouterMembreCommand(
                uuid_jury=str(self.doctorate_uuid),
                **serializer.data,
            )
        )
        return Response({'uuid': result}, status=status.HTTP_201_CREATED)


class JuryMemberDetailSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'GET': MembreJuryDTOSerializer,
        'PUT': (ModifierMembreCommandSerializer, JuryIdentityDTOSerializer),
        'PATCH': (ModifierRoleMembreCommandSerializer, JuryIdentityDTOSerializer),
        'DELETE': None,
    }

    method_mapping = {
        'get': 'retrieve',
        'put': 'update',
        'patch': 'update_role',
        'delete': 'remove',
    }

    operation_id_base = '_jury_member'


class JuryMemberDetailAPIView(
    DoctorateAPIPermissionRequiredMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericAPIView,
):
    name = "jury-member-detail"
    schema = JuryMemberDetailSchema()
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.view_jury',
        'PUT': 'parcours_doctoral.change_jury',
        'PATCH': 'parcours_doctoral.change_jury',
        'DELETE': 'parcours_doctoral.change_jury',
    }

    def get(self, request, *args, **kwargs):
        """Get the members of a jury"""
        membre = message_bus_instance.invoke(
            RecupererJuryMembreQuery(
                uuid_jury=str(self.doctorate_uuid),
                uuid_membre=str(self.kwargs['member_uuid']),
            )
        )
        serializer = MembreJuryDTOSerializer(instance=membre)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        """Update a member of the jury"""
        serializer = ModifierMembreCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = message_bus_instance.invoke(
            ModifierMembreCommand(
                uuid_jury=str(self.doctorate_uuid),
                uuid_membre=str(self.kwargs['member_uuid']),
                **serializer.data,
            )
        )
        serializer = JuryIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        """Update the role of a member of the jury"""
        serializer = ModifierRoleMembreCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = message_bus_instance.invoke(
            ModifierRoleMembreCommand(
                uuid_jury=str(self.doctorate_uuid),
                uuid_membre=str(self.kwargs['member_uuid']),
                **serializer.data,
            )
        )
        serializer = JuryIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """Remove a member"""
        message_bus_instance.invoke(
            RetirerMembreCommand(
                uuid_jury=str(self.doctorate_uuid),
                uuid_membre=str(self.kwargs['member_uuid']),
            )
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
