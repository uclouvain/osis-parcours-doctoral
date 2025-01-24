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

from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.api.permissions import DoctorateAPIPermissionRequiredMixin
from parcours_doctoral.api.schema import ResponseSpecificSchema
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


class ConfirmationSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'GET': ConfirmationPaperDTOSerializer,
    }

    def get_operation_id(self, path, method):
        if method == 'GET':
            return 'retrieve_confirmation_papers'
        return super().get_operation_id(path, method)


class ConfirmationAPIView(DoctorateAPIPermissionRequiredMixin, GenericAPIView):
    name = "confirmation"
    schema = ConfirmationSchema()
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.view_confirmation',
    }

    def get(self, request, *args, **kwargs):
        """Get the confirmation papers related to the doctorate"""
        confirmation_papers = message_bus_instance.invoke(
            RecupererEpreuvesConfirmationQuery(parcours_doctoral_uuid=kwargs.get('uuid')),
        )
        serializer = ConfirmationPaperDTOSerializer(instance=confirmation_papers, many=True)
        return Response(serializer.data)


class LastConfirmationSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'GET': ConfirmationPaperDTOSerializer,
        'POST': (
            SubmitConfirmationPaperExtensionRequestCommandSerializer,
            ParcoursDoctoralIdentityDTOSerializer,
        ),
        'PUT': (
            SubmitConfirmationPaperCommandSerializer,
            ParcoursDoctoralIdentityDTOSerializer,
        ),
    }

    def get_operation_id(self, path, method):
        return {
            'GET': 'retrieve_last_confirmation_paper',
            'POST': 'submit_confirmation_paper_extension_request',
            'PUT': 'submit_confirmation_paper',
        }.get(method) or super().get_operation_id(path, method)


class LastConfirmationAPIView(DoctorateAPIPermissionRequiredMixin, mixins.RetrieveModelMixin, GenericAPIView):
    name = "last_confirmation"
    schema = LastConfirmationSchema()
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.view_confirmation',
        'PUT': 'parcours_doctoral.change_confirmation',
        'POST': 'parcours_doctoral.change_confirmation_extension',
    }

    def get_last_confirmation_paper(self):
        return message_bus_instance.invoke(
            RecupererDerniereEpreuveConfirmationQuery(parcours_doctoral_uuid=self.doctorate_uuid),
        )

    def get(self, request, *args, **kwargs):
        """Get the last confirmation paper related to the doctorate"""
        last_confirmation_paper = self.get_last_confirmation_paper()
        serializer = ConfirmationPaperDTOSerializer(instance=last_confirmation_paper)
        return Response(serializer.data)

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


class LastConfirmationCanvasSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'GET': ConfirmationPaperCanvasSerializer,
    }

    def get_operation_id(self, path, method):
        return 'retrieve_last_confirmation_paper_canvas'


class LastConfirmationCanvasAPIView(DoctorateAPIPermissionRequiredMixin, mixins.RetrieveModelMixin, GenericAPIView):
    name = "last_confirmation_canvas"
    schema = LastConfirmationCanvasSchema()
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.view_confirmation',
    }

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
            },
        )

        serializer = ConfirmationPaperCanvasSerializer(instance={'uuid': uuid})

        return Response(serializer.data)


class PromoterConfirmationSchema(ResponseSpecificSchema):
    serializer_mapping = {
        'PUT': (
            CompleteConfirmationPaperByPromoterCommandSerializer,
            ParcoursDoctoralIdentityDTOSerializer,
        ),
    }

    def get_operation_id(self, path, method):
        return 'complete_confirmation_paper_by_promoter'


class SupervisedConfirmationAPIView(
    DoctorateAPIPermissionRequiredMixin,
    mixins.UpdateModelMixin,
    GenericAPIView,
):
    name = "supervised_confirmation"
    schema = PromoterConfirmationSchema()
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'PUT': 'parcours_doctoral.upload_pdf_confirmation',
    }

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
