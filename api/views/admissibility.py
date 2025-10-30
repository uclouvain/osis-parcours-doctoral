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
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.response import Response

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.api.permissions import DoctorateAPIPermissionRequiredMixin
from parcours_doctoral.api.serializers import ParcoursDoctoralIdentityDTOSerializer
from parcours_doctoral.api.serializers.admissibility import *
from parcours_doctoral.ddd.recevabilite.commands import (
    RecupererRecevabilitesQuery,
    SoumettreRecevabiliteCommand,
)
from parcours_doctoral.exports.admissibility_minutes_canvas import (
    admissibility_minutes_canvas_url,
)

__all__ = [
    "AdmissibilityListAPIView",
    "AdmissibilityMinutesAPIView",
]


class AdmissibilityListAPIView(DoctorateAPIPermissionRequiredMixin, GenericAPIView):
    name = "admissibility-list"
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.api_view_admissibility',
        'PUT': 'parcours_doctoral.api_change_admissibility',
    }
    serializer_class = AdmissibilityDTOSerializer

    @extend_schema(
        responses=AdmissibilityDTOSerializer(many=True),
        operation_id='retrieve_admissibilities',
    )
    def get(self, request, *args, **kwargs):
        """Get the admissibilities related to the doctorate"""
        admissibilities = message_bus_instance.invoke(
            RecupererRecevabilitesQuery(parcours_doctoral_uuid=self.kwargs['uuid'])
        )
        serializer = AdmissibilityDTOSerializer(instance=admissibilities, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=SubmitAdmissibilitySerializer,
        responses=ParcoursDoctoralIdentityDTOSerializer,
        operation_id='submit_admissibility',
    )
    def put(self, request, *args, **kwargs):
        """Submit an admissibility"""
        serializer = SubmitAdmissibilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = message_bus_instance.invoke(
            SoumettreRecevabiliteCommand(
                parcours_doctoral_uuid=self.kwargs['uuid'],
                matricule_auteur=self.request.user.person.global_id,
                **serializer.validated_data,
            )
        )

        serializer = ParcoursDoctoralIdentityDTOSerializer(instance=result)

        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        responses=AdmissibilityMinutesCanvasSerializer,
        operation_id='retrieve_admissibility_minutes_canvas',
    ),
)
class AdmissibilityMinutesAPIView(DoctorateAPIPermissionRequiredMixin, RetrieveAPIView):
    name = "admissibility-minutes"
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.api_view_admissibility_minutes',
    }
    serializer_class = AdmissibilityMinutesCanvasSerializer

    def get_object(self):
        doctorate = self.get_permission_object()

        url = admissibility_minutes_canvas_url(
            doctorate_uuid=self.doctorate_uuid,
            language=doctorate.student.language,
        )

        return {'url': url}
