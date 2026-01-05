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
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.api.permissions import DoctorateAPIPermissionRequiredMixin
from parcours_doctoral.api.serializers import ParcoursDoctoralIdentityDTOSerializer
from parcours_doctoral.api.serializers.authorization_distribution import *
from parcours_doctoral.ddd.autorisation_diffusion_these.commands import (
    EncoderFormulaireAutorisationDiffusionTheseCommand,
    EnvoyerFormulaireAutorisationDiffusionTheseAuPromoteurReferenceCommand,
    RecupererAutorisationDiffusionTheseQuery,
)

__all__ = [
    "AuthorizationDistributionAPIView",
]


class AuthorizationDistributionAPIView(DoctorateAPIPermissionRequiredMixin, GenericAPIView):
    name = "authorization-distribution"
    permission_mapping = {
        'GET': 'parcours_doctoral.api_view_authorization_distribution',
        'PUT': 'parcours_doctoral.api_change_authorization_distribution',
        'POST': 'parcours_doctoral.api_change_authorization_distribution',
    }
    serializer_class = AuthorizationDistributionDTOSerializer

    @extend_schema(
        responses=AuthorizationDistributionDTOSerializer,
        operation_id='retrieve_authorization_distribution',
    )
    def get(self, request, *args, **kwargs):
        """Get the distribution authorization data related to the doctorate"""
        authorization_distribution = message_bus_instance.invoke(
            RecupererAutorisationDiffusionTheseQuery(uuid_parcours_doctoral=str(self.kwargs['uuid']))
        )
        serializer = AuthorizationDistributionDTOSerializer(instance=authorization_distribution)
        return Response(serializer.data)

    @extend_schema(
        request=UpdateAuthorizationDistributionSerializer,
        responses=ParcoursDoctoralIdentityDTOSerializer,
        operation_id='update_authorization_distribution',
    )
    def put(self, request, *args, **kwargs):
        """Update the authorization_distribution"""
        serializer = UpdateAuthorizationDistributionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = message_bus_instance.invoke(
            EncoderFormulaireAutorisationDiffusionTheseCommand(
                uuid_parcours_doctoral=str(self.kwargs['uuid']),
                **serializer.validated_data,
            )
        )

        serializer = ParcoursDoctoralIdentityDTOSerializer(instance=result)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=SendAuthorizationDistributionToPromoterSerializer,
        responses=ParcoursDoctoralIdentityDTOSerializer,
        operation_id='send_authorization_distribution_to_promoter',
    )
    def post(self, request, *args, **kwargs):
        """Update the authorization_distribution and send it to the lead supervisor"""
        serializer = UpdateAuthorizationDistributionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = message_bus_instance.invoke(
            EnvoyerFormulaireAutorisationDiffusionTheseAuPromoteurReferenceCommand(
                uuid_parcours_doctoral=str(self.kwargs['uuid']),
                **serializer.validated_data,
            )
        )

        serializer = ParcoursDoctoralIdentityDTOSerializer(instance=result)

        return Response(serializer.data, status=status.HTTP_200_OK)
