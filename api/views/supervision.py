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

from rest_framework import mixins
from rest_framework.generics import GenericAPIView
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.api import serializers
from parcours_doctoral.api.permissions import DoctorateAPIPermissionRequiredMixin
from parcours_doctoral.api.schema import ResponseSpecificSchema
from parcours_doctoral.ddd.commands import (
    GetGroupeDeSupervisionQuery,
    RecupererParcoursDoctoralQuery,
)
from parcours_doctoral.exports.supervision_canvas import supervision_canvas_pdf

__all__ = [
    "SupervisionAPIView",
    "SupervisionCanvasApiView",
]


class SupervisionSchema(ResponseSpecificSchema):
    operation_id_base = '_supervision'
    serializer_mapping = {
        'GET': serializers.SupervisionDTOSerializer,
    }


class SupervisionAPIView(
    DoctorateAPIPermissionRequiredMixin,
    mixins.RetrieveModelMixin,
    GenericAPIView,
):
    name = "supervision"
    schema = SupervisionSchema()
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.view_supervision',
    }

    def get(self, request, *args, **kwargs):
        """Get the supervision group of the PhD"""
        supervision = message_bus_instance.invoke(
            GetGroupeDeSupervisionQuery(uuid_parcours_doctoral=self.doctorate_uuid),
        )
        serializer = serializers.SupervisionDTOSerializer(instance=supervision)
        return Response(serializer.data)


class SupervisionCanvasSchema(ResponseSpecificSchema):
    operation_id_base = '_supervision_canvas'
    serializer_mapping = {
        'GET': serializers.SupervisionCanvasSerializer,
    }


class SupervisionCanvasApiView(SupervisionAPIView):
    name = "supervision_canvas"
    schema = SupervisionCanvasSchema()
    permission_mapping = {
        'GET': 'parcours_doctoral.view_supervision_canvas',
    }
    renderer_classes = [JSONRenderer]

    def get(self, request, *args, **kwargs):
        """Get the supervision group of the PhD"""
        doctorate_object = self.get_permission_object()

        doctorate_dto = message_bus_instance.invoke(
            RecupererParcoursDoctoralQuery(parcours_doctoral_uuid=self.doctorate_uuid),
        )

        url = supervision_canvas_pdf(
            parcours_doctoral=doctorate_dto,
            language=doctorate_object.student.language,
        )

        serializer = serializers.SupervisionCanvasSerializer(data={'url': url})

        serializer.is_valid()

        return Response(data=serializer.data)
