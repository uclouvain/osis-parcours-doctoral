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

from datetime import timedelta

from django.utils.functional import cached_property
from django.utils.timezone import now
from drf_spectacular.utils import extend_schema
from osis_signature.utils import get_actor_from_token
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.api.serializers import ExternalSupervisionDTOSerializer
from parcours_doctoral.ddd.commands import (
    GetGroupeDeSupervisionQuery,
    RecupererParcoursDoctoralQuery,
)
from parcours_doctoral.utils.cache import get_cached_parcours_doctoral_perm_obj

__all__ = [
    'ExternalDoctorateSupervisionAPIView',
]


class ExternalDoctorateAPIView(APIView):
    authentication_classes = []
    permission_classes = []
    EXTERNAL_ACTOR_TOKEN_EXPIRATION_DAYS = 7

    @property
    def doctorate_uuid(self):
        return self.kwargs['uuid']

    def get_permission_object(self):
        return get_cached_parcours_doctoral_perm_obj(self.doctorate_uuid)

    @cached_property
    def actor(self):
        return get_actor_from_token(self.kwargs['token'])

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        doctorate = self.get_permission_object()

        # Load actor from token
        if (
            not doctorate.is_initialized
            or not self.actor
            # must be part of supervision group
            or self.actor.process_id != doctorate.supervision_group_id
            # must be not older than 7 days
            or self.actor.states.last().created_at
            < now()
            - timedelta(
                days=self.EXTERNAL_ACTOR_TOKEN_EXPIRATION_DAYS,
            )
        ):
            raise PermissionDenied

        # Override the request data to use the actor's uuid loaded from token
        request.data['uuid_membre'] = str(self.actor.uuid)


class ExternalDoctorateSupervisionAPIView(ExternalDoctorateAPIView):
    name = 'external-supervision'

    @extend_schema(
        responses=ExternalSupervisionDTOSerializer,
        operation_id='retrieve_external_doctorate_supervision',
    )
    def get(self, request, *args, **kwargs):
        """Returns necessary info about the doctorate and the supervision."""
        doctorate, supervision = message_bus_instance.invoke_multiple(
            [
                RecupererParcoursDoctoralQuery(parcours_doctoral_uuid=self.doctorate_uuid),
                GetGroupeDeSupervisionQuery(uuid_parcours_doctoral=self.doctorate_uuid),
            ],
        )

        serializer = ExternalSupervisionDTOSerializer(
            instance={
                'parcours_doctoral': doctorate,
                'supervision': supervision,
            },
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
