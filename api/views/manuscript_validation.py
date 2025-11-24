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
from parcours_doctoral.api.serializers.manuscript_validation import *
from parcours_doctoral.ddd.autorisation_diffusion_these.commands import (
    AccepterTheseParPromoteurReferenceCommand,
    RefuserTheseParPromoteurReferenceCommand,
)

__all__ = [
    "ManuscriptValidationApiView",
]


class ManuscriptValidationApiView(DoctorateAPIPermissionRequiredMixin, GenericAPIView):
    name = "manuscript-validation"
    permission_mapping = {
        'PUT': 'parcours_doctoral.api_validate_manuscript',
        'POST': 'parcours_doctoral.api_validate_manuscript',
    }
    serializer_class = RejectThesisByLeadPromoterSerializer

    @extend_schema(
        request=RejectThesisByLeadPromoterSerializer,
        responses=ParcoursDoctoralIdentityDTOSerializer,
        operation_id='reject_thesis_by_lead_promoter',
    )
    def put(self, request, *args, **kwargs):
        """Reject the thesis (lead promoter)"""
        serializer = RejectThesisByLeadPromoterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = message_bus_instance.invoke(
            RefuserTheseParPromoteurReferenceCommand(
                uuid_parcours_doctoral=str(self.kwargs['uuid']),
                matricule_promoteur=self.request.user.person.global_id,
                **serializer.validated_data,
            )
        )

        serializer = ParcoursDoctoralIdentityDTOSerializer(instance=result)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=AcceptThesisByLeadPromoterSerializer,
        responses=ParcoursDoctoralIdentityDTOSerializer,
        operation_id='accept_thesis_by_lead_promoter',
    )
    def post(self, request, *args, **kwargs):
        """Accept the thesis (lead promoter)"""
        serializer = AcceptThesisByLeadPromoterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = message_bus_instance.invoke(
            AccepterTheseParPromoteurReferenceCommand(
                uuid_parcours_doctoral=str(self.kwargs['uuid']),
                matricule_promoteur=self.request.user.person.global_id,
                **serializer.validated_data,
            )
        )

        serializer = ParcoursDoctoralIdentityDTOSerializer(instance=result)

        return Response(serializer.data, status=status.HTTP_200_OK)
