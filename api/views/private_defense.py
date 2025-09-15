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
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.response import Response

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.api.permissions import DoctorateAPIPermissionRequiredMixin
from parcours_doctoral.api.serializers import ParcoursDoctoralIdentityDTOSerializer
from parcours_doctoral.api.serializers.private_defense import (
    PrivateDefenseDTOSerializer,
    PrivateDefenseMinutesCanvasSerializer,
    SubmitPrivateDefenseMinutesSerializer,
    SubmitPrivateDefenseSerializer,
)
from parcours_doctoral.ddd.defense_privee.commands import (
    RecupererDefensePriveeQuery,
    RecupererDefensesPriveesQuery,
    SoumettreDefensePriveeCommand,
    SoumettreProcesVerbalDefensePriveeCommand,
)
from parcours_doctoral.exports.private_defense_minutes_canvas import (
    private_defense_minutes_canvas_url,
)

__all__ = [
    "PrivateDefenseListAPIView",
    "PrivateDefenseAPIView",
    "PrivateDefenseMinutesAPIView",
]


class PrivateDefenseListAPIView(DoctorateAPIPermissionRequiredMixin, GenericAPIView):
    name = "private-defense-list"
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.api_view_private_defense',
        'PUT': 'parcours_doctoral.api_change_private_defense',
    }
    serializer_class = PrivateDefenseDTOSerializer

    @extend_schema(
        responses=PrivateDefenseDTOSerializer(many=True),
        operation_id='retrieve_private_defenses',
    )
    def get(self, request, *args, **kwargs):
        """Get the private defenses related to the doctorate"""
        private_defenses = message_bus_instance.invoke(
            RecupererDefensesPriveesQuery(parcours_doctoral_uuid=kwargs.get('uuid')),
        )
        serializer = PrivateDefenseDTOSerializer(instance=private_defenses, many=True)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        """Only used for permissions"""
        return Response()


class PrivateDefenseAPIView(DoctorateAPIPermissionRequiredMixin, mixins.RetrieveModelMixin, GenericAPIView):
    name = "private-defense"
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.api_view_private_defense',
        'PUT': 'parcours_doctoral.api_change_private_defense',
    }
    serializer_class = PrivateDefenseDTOSerializer

    @extend_schema(
        responses=PrivateDefenseDTOSerializer,
        operation_id='retrieve_private_defense',
    )
    def get(self, request, *args, **kwargs):
        """Get a single private defense"""
        private_defense = message_bus_instance.invoke(
            RecupererDefensePriveeQuery(
                uuid=self.kwargs['private_defense_uuid'],
            )
        )
        serializer = PrivateDefenseDTOSerializer(instance=private_defense)
        return Response(serializer.data)

    @extend_schema(
        request=SubmitPrivateDefenseSerializer,
        responses=ParcoursDoctoralIdentityDTOSerializer,
        operation_id='submit_private_defense',
    )
    def put(self, request, *args, **kwargs):
        """Submit a private defense"""
        serializer = SubmitPrivateDefenseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = message_bus_instance.invoke(
            SoumettreDefensePriveeCommand(
                uuid=self.kwargs['private_defense_uuid'],
                matricule_auteur=self.request.user.person.global_id,
                **serializer.validated_data,
            )
        )

        serializer = ParcoursDoctoralIdentityDTOSerializer(instance=result)

        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        responses=PrivateDefenseMinutesCanvasSerializer,
        operation_id='retrieve_private_defense_minutes_canvas',
    ),
    put=extend_schema(
        request=SubmitPrivateDefenseMinutesSerializer,
        responses=ParcoursDoctoralIdentityDTOSerializer,
        operation_id='submit_private_defense_minutes',
    ),
)
class PrivateDefenseMinutesAPIView(DoctorateAPIPermissionRequiredMixin, RetrieveAPIView):
    name = "private-defense-minutes"
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.api_view_private_defense_minutes',
        'PUT': 'parcours_doctoral.api_upload_private_defense_minutes',
    }
    serializer_class = PrivateDefenseMinutesCanvasSerializer

    def get_object(self):
        doctorate = self.get_permission_object()

        url = private_defense_minutes_canvas_url(
            doctorate_uuid=self.doctorate_uuid,
            language=doctorate.student.language,
        )

        return {'url': url}

    def put(self, request, *args, **kwargs):
        """Submit the minutes of the private defense"""
        serializer = SubmitPrivateDefenseMinutesSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        result = message_bus_instance.invoke(
            SoumettreProcesVerbalDefensePriveeCommand(
                matricule_auteur=self.request.user.person.global_id,
                **serializer.validated_data,
            )
        )

        serializer = ParcoursDoctoralIdentityDTOSerializer(instance=result)

        return Response(serializer.data, status=status.HTTP_200_OK)
