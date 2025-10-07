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
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.api.permissions import DoctorateAPIPermissionRequiredMixin
from parcours_doctoral.api.serializers import ParcoursDoctoralIdentityDTOSerializer
from parcours_doctoral.api.serializers.public_defense import (
    PublicDefenseMinutesCanvasSerializer,
    SubmitPublicDefenseMinutesSerializer,
    SubmitPublicDefenseSerializer,
)
from parcours_doctoral.ddd.soutenance_publique.commands import (
    SoumettreProcesVerbalSoutenancePubliqueCommand,
    SoumettreSoutenancePubliqueCommand,
)
from parcours_doctoral.exports.public_defense_minutes_canvas import (
    public_defense_minutes_canvas_url,
)

__all__ = [
    "PublicDefenseAPIView",
    "PublicDefenseMinutesAPIView",
]


class PublicDefenseAPIView(DoctorateAPIPermissionRequiredMixin, RetrieveAPIView):
    name = "public-defense"
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.api_view_public_defense',
        'PUT': 'parcours_doctoral.api_change_public_defense',
    }
    serializer_class = ParcoursDoctoralIdentityDTOSerializer

    @extend_schema(exclude=True)
    def get(self, request, *args, **kwargs):
        """Only used for permissions"""
        return Response()

    @extend_schema(
        request=SubmitPublicDefenseSerializer,
        responses=ParcoursDoctoralIdentityDTOSerializer,
        operation_id='submit_public_defense',
    )
    def put(self, request, *args, **kwargs):
        """Submit a public defense"""
        serializer = SubmitPublicDefenseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = message_bus_instance.invoke(
            SoumettreSoutenancePubliqueCommand(
                uuid_parcours_doctoral=self.doctorate_uuid,
                matricule_auteur=self.request.user.person.global_id,
                **serializer.validated_data,
            )
        )

        serializer = ParcoursDoctoralIdentityDTOSerializer(instance=result)

        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        responses=PublicDefenseMinutesCanvasSerializer,
        operation_id='retrieve_public_defense_minutes_canvas',
    ),
    put=extend_schema(
        request=SubmitPublicDefenseMinutesSerializer,
        responses=ParcoursDoctoralIdentityDTOSerializer,
        operation_id='submit_public_defense_minutes',
    ),
)
class PublicDefenseMinutesAPIView(DoctorateAPIPermissionRequiredMixin, RetrieveAPIView):
    name = "public-defense-minutes"
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.api_view_public_defense_minutes',
        'PUT': 'parcours_doctoral.api_upload_public_defense_minutes',
    }
    serializer_class = PublicDefenseMinutesCanvasSerializer

    def get_object(self):
        doctorate = self.get_permission_object()

        url = public_defense_minutes_canvas_url(
            doctorate_uuid=self.doctorate_uuid,
            language=doctorate.student.language,
        )

        return {'url': url}

    def put(self, request, *args, **kwargs):
        """Submit the minutes of the public defense"""
        serializer = SubmitPublicDefenseMinutesSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        result = message_bus_instance.invoke(
            SoumettreProcesVerbalSoutenancePubliqueCommand(
                uuid_parcours_doctoral=self.doctorate_uuid,
                matricule_auteur=self.request.user.person.global_id,
                **serializer.validated_data,
            )
        )

        serializer = ParcoursDoctoralIdentityDTOSerializer(instance=result)

        return Response(serializer.data, status=status.HTTP_200_OK)
