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
    CompleteConfirmationPaperByPromoterCommandSerializer,
    ConfirmationPaperCanvasSerializer,
    ConfirmationPaperDTOSerializer,
    ParcoursDoctoralIdentityDTOSerializer,
    SubmitConfirmationPaperCommandSerializer,
    SubmitConfirmationPaperExtensionRequestCommandSerializer,
)
from parcours_doctoral.ddd.commands import (
    GetGroupeDeSupervisionQuery,
    RecupererParcoursDoctoralQuery,
)
from parcours_doctoral.ddd.epreuve_confirmation.commands import (
    CompleterEpreuveConfirmationParPromoteurCommand,
    RecupererDerniereEpreuveConfirmationQuery,
    RecupererEpreuvesConfirmationQuery,
    SoumettreEpreuveConfirmationCommand,
    SoumettreReportDeDateCommand,
)
from parcours_doctoral.exports.confirmation_canvas import (
    parcours_doctoral_pdf_confirmation_canvas,
)

__all__ = [
    "ConfirmationAPIView",
    "LastConfirmationAPIView",
    "LastConfirmationCanvasAPIView",
    "SupervisedConfirmationAPIView",
]

from parcours_doctoral.models import Activity


class ConfirmationAPIView(DoctorateAPIPermissionRequiredMixin, GenericAPIView):
    name = "confirmation"
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.api_view_confirmation',
    }

    @extend_schema(
        responses=ConfirmationPaperDTOSerializer(many=True),
        operation_id='retrieve_confirmation_papers',
    )
    def get(self, request, *args, **kwargs):
        """Get the confirmation papers related to the doctorate"""
        confirmation_papers = message_bus_instance.invoke(
            RecupererEpreuvesConfirmationQuery(parcours_doctoral_uuid=kwargs.get('uuid')),
        )
        serializer = ConfirmationPaperDTOSerializer(instance=confirmation_papers, many=True)
        return Response(serializer.data)


class LastConfirmationAPIView(DoctorateAPIPermissionRequiredMixin, mixins.RetrieveModelMixin, GenericAPIView):
    name = "last_confirmation"
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.api_view_confirmation',
        'PUT': 'parcours_doctoral.api_change_confirmation',
        'POST': 'parcours_doctoral.api_change_confirmation_extension',
    }

    def get_last_confirmation_paper(self):
        return message_bus_instance.invoke(
            RecupererDerniereEpreuveConfirmationQuery(parcours_doctoral_uuid=self.doctorate_uuid),
        )

    @extend_schema(
        responses=ConfirmationPaperDTOSerializer,
        operation_id='retrieve_last_confirmation_paper',
    )
    def get(self, request, *args, **kwargs):
        """Get the last confirmation paper related to the doctorate"""
        last_confirmation_paper = self.get_last_confirmation_paper()
        serializer = ConfirmationPaperDTOSerializer(instance=last_confirmation_paper)
        return Response(serializer.data)

    @extend_schema(
        request=SubmitConfirmationPaperCommandSerializer,
        responses=ParcoursDoctoralIdentityDTOSerializer,
        operation_id='submit_confirmation_paper',
    )
    def put(self, request, *args, **kwargs):
        """Submit the last confirmation paper related to a doctorate"""
        serializer = SubmitConfirmationPaperCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        last_confirmation_paper = self.get_last_confirmation_paper()
        doctorate = self.get_permission_object()

        result = message_bus_instance.invoke(
            SoumettreEpreuveConfirmationCommand(
                uuid=last_confirmation_paper.uuid,
                matricule_auteur=doctorate.student.global_id,
                **serializer.validated_data,
            )
        )

        serializer = ParcoursDoctoralIdentityDTOSerializer(instance=result)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=SubmitConfirmationPaperExtensionRequestCommandSerializer,
        responses=ParcoursDoctoralIdentityDTOSerializer,
        operation_id='submit_confirmation_paper_extension_request',
    )
    def post(self, request, *args, **kwargs):
        """Submit the extension request of the last confirmation paper of a doctorate"""
        serializer = SubmitConfirmationPaperExtensionRequestCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        last_confirmation_paper = self.get_last_confirmation_paper()

        result = message_bus_instance.invoke(
            SoumettreReportDeDateCommand(
                uuid=last_confirmation_paper.uuid,
                **serializer.validated_data,
            )
        )

        serializer = ParcoursDoctoralIdentityDTOSerializer(instance=result)

        return Response(serializer.data, status=status.HTTP_200_OK)


class LastConfirmationCanvasAPIView(DoctorateAPIPermissionRequiredMixin, mixins.RetrieveModelMixin, GenericAPIView):
    name = "last_confirmation_canvas"
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.api_view_confirmation',
    }

    @extend_schema(
        responses=ConfirmationPaperCanvasSerializer,
        operation_id='retrieve_last_confirmation_paper_canvas',
    )
    def get(self, request, *args, **kwargs):
        """Get the last confirmation paper canvas related to the doctorate"""
        parcours_doctoral, confirmation_paper, supervision_group = message_bus_instance.invoke_multiple(
            [
                RecupererParcoursDoctoralQuery(self.doctorate_uuid),
                RecupererDerniereEpreuveConfirmationQuery(parcours_doctoral_uuid=self.doctorate_uuid),
                GetGroupeDeSupervisionQuery(uuid_parcours_doctoral=self.doctorate_uuid),
            ]
        )
        doctorate = self.get_permission_object()

        doctoral_training_ects_nb = Activity.objects.get_doctoral_training_credits_number(
            parcours_doctoral_uuid=self.doctorate_uuid,
        )

        has_additional_training = Activity.objects.has_complementary_training(
            parcours_doctoral_uuid=self.doctorate_uuid,
        )

        uuid = parcours_doctoral_pdf_confirmation_canvas(
            parcours_doctoral=doctorate,
            language=doctorate.student.language,
            context={
                'parcours_doctoral': parcours_doctoral,
                'confirmation_paper': confirmation_paper,
                'supervision_group': supervision_group,
                'supervision_people_nb': (
                    len(supervision_group.signatures_promoteurs) + len(supervision_group.signatures_membres_CA)
                ),
                'doctoral_training_ects_nb': doctoral_training_ects_nb,
                'has_additional_training': has_additional_training,
            },
        )

        serializer = ConfirmationPaperCanvasSerializer(instance={'uuid': uuid})

        return Response(serializer.data)


class SupervisedConfirmationAPIView(
    DoctorateAPIPermissionRequiredMixin,
    mixins.UpdateModelMixin,
    GenericAPIView,
):
    name = "supervised_confirmation"
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'PUT': 'parcours_doctoral.api_upload_pdf_confirmation',
    }

    @extend_schema(
        request=CompleteConfirmationPaperByPromoterCommandSerializer,
        responses=ParcoursDoctoralIdentityDTOSerializer,
        operation_id='complete_confirmation_paper_by_promoter',
    )
    def put(self, request, *args, **kwargs):
        """Complete the confirmation paper related to a parcours_doctoral"""
        serializer = CompleteConfirmationPaperByPromoterCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        last_confirmation_paper = message_bus_instance.invoke(
            RecupererDerniereEpreuveConfirmationQuery(parcours_doctoral_uuid=self.doctorate_uuid),
        )

        result = message_bus_instance.invoke(
            CompleterEpreuveConfirmationParPromoteurCommand(
                uuid=last_confirmation_paper.uuid,
                **serializer.validated_data,
            )
        )

        serializer = ParcoursDoctoralIdentityDTOSerializer(instance=result)

        return Response(serializer.data, status=status.HTTP_200_OK)
