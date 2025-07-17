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
from parcours_doctoral.api.permissions import DoctorateAPIPermissionRequiredMixin
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


class JuryPreparationAPIView(
    DoctorateAPIPermissionRequiredMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericAPIView,
):
    name = "jury-preparation"
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.api_view_jury',
        'POST': 'parcours_doctoral.api_change_jury',
    }

    @extend_schema(
        responses=JuryDTOSerializer,
        operation_id='retrieve_jury_preparation',
    )
    def get(self, request, *args, **kwargs):
        """Get the Jury of a doctorate"""
        jury = message_bus_instance.invoke(RecupererJuryQuery(uuid_jury=self.doctorate_uuid))
        serializer = JuryDTOSerializer(instance=jury)
        return Response(serializer.data)

    @extend_schema(
        request=ModifierJuryCommandSerializer,
        responses=JuryIdentityDTOSerializer,
        operation_id='update_jury_preparation',
    )
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


class JuryMembersListAPIView(
    DoctorateAPIPermissionRequiredMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericAPIView,
):
    name = "jury-members-list"
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.api_view_jury',
        'POST': 'parcours_doctoral.api_change_jury',
    }

    @extend_schema(
        responses=MembreJuryDTOSerializer,
        operation_id='list_jury_members',
    )
    def get(self, request, *args, **kwargs):
        """Get the members of a jury"""
        jury = message_bus_instance.invoke(RecupererJuryQuery(uuid_jury=self.doctorate_uuid))
        serializer = MembreJuryDTOSerializer(instance=jury.membres, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=AjouterMembreCommandSerializer,
        responses=MembreJuryIdentityDTOSerializer,
        operation_id='create_jury_members',
    )
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


class JuryMemberDetailAPIView(
    DoctorateAPIPermissionRequiredMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericAPIView,
):
    name = "jury-member-detail"
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.api_view_jury',
        'PUT': 'parcours_doctoral.api_change_jury',
        'PATCH': 'parcours_doctoral.api_change_jury',
        'DELETE': 'parcours_doctoral.api_change_jury',
    }

    @extend_schema(
        responses=MembreJuryDTOSerializer,
        operation_id='retrieve_jury_member',
    )
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

    @extend_schema(
        request=ModifierMembreCommandSerializer,
        responses=JuryIdentityDTOSerializer,
        operation_id='update_jury_member',
    )
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

    @extend_schema(
        request=ModifierRoleMembreCommandSerializer,
        responses=JuryIdentityDTOSerializer,
        operation_id='update_role_jury_member',
    )
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

    @extend_schema(
        request=None,
        responses=None,
        operation_id='remove_jury_member',
    )
    def delete(self, request, *args, **kwargs):
        """Remove a member"""
        message_bus_instance.invoke(
            RetirerMembreCommand(
                uuid_jury=str(self.doctorate_uuid),
                uuid_membre=str(self.kwargs['member_uuid']),
            )
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
