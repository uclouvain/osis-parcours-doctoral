# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from rest_framework import mixins
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from parcours_doctoral.api import serializers
from parcours_doctoral.api.schema import ResponseSpecificSchema

from parcours_doctoral.utils import get_cached_parcours_doctoral_perm_obj
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin
from parcours_doctoral.ddd.commands import RecupererParcoursDoctoralQuery


class DoctorateSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'GET': serializers.ParcoursDoctoralDTOSerializer,
    }


class DoctorateAPIView(
    APIPermissionRequiredMixin,
    mixins.RetrieveModelMixin,
    GenericAPIView,
):
    name = "doctorate"
    pagination_class = None
    filter_backends = []
    schema = DoctorateSchema()
    permission_mapping = {
        'GET': 'admission.view_doctorateadmission',
    }

    def get_permission_object(self):
        return get_cached_parcours_doctoral_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Get the parcours doctoral"""
        parcours_doctoral = message_bus_instance.invoke(
            RecupererParcoursDoctoralQuery(parcours_doctoral_uuid=kwargs.get('uuid')),
        )
        serializer = serializers.ParcoursDoctoralDTOSerializer(
            instance=parcours_doctoral,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data)
