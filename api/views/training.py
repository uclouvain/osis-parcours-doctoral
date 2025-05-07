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
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    PolymorphicProxySerializer,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.settings import api_settings

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.api import serializers
from parcours_doctoral.api.permissions import DoctorateAPIPermissionRequiredMixin
from parcours_doctoral.api.serializers import InscriptionEvaluationDTOSerializer
from parcours_doctoral.api.serializers.activity import (
    DoctoralTrainingActivitySerializer,
    DoctoralTrainingAssentSerializer,
    DoctoralTrainingBatchSerializer,
    DoctoralTrainingConfigSerializer,
)
from parcours_doctoral.api.serializers.training import TrainingRecapPdfSerializer
from parcours_doctoral.ddd.commands import RecupererParcoursDoctoralQuery
from parcours_doctoral.ddd.formation.commands import (
    DonnerAvisSurActiviteCommand,
    RecupererInscriptionEvaluationQuery,
    RecupererInscriptionsEvaluationsQuery,
    SoumettreActivitesCommand,
    SupprimerActiviteCommand,
)
from parcours_doctoral.ddd.formation.domain.model.enums import StatutActivite
from parcours_doctoral.exports.training_recap import (
    parcours_doctoral_pdf_formation_doctorale,
)
from parcours_doctoral.models.activity import Activity
from parcours_doctoral.models.cdd_config import CddConfiguration

__all__ = [
    "DoctoralTrainingListView",
    "TrainingConfigView",
    "TrainingView",
    "TrainingSubmitView",
    "TrainingAssentView",
    "ComplementaryTrainingListView",
    "CourseEnrollmentListView",
    "AssessmentEnrollmentListView",
    "AssessmentEnrollmentDetailView",
    "TrainingRecapPdfApiView",
]


DoctoralTrainingActivitySerializerScheme = PolymorphicProxySerializer(
    component_name='DoctoralTrainingActivity',
    serializers={
        'Conference': serializers.ConferenceSerializer,
        'ConferenceCommunication': serializers.ConferenceCommunicationSerializer,
        'ConferencePublication': serializers.ConferencePublicationSerializer,
        'Residency': serializers.ResidencySerializer,
        'ResidencyCommunication': serializers.ResidencyCommunicationSerializer,
        'Communication': serializers.CommunicationSerializer,
        'Publication': serializers.PublicationSerializer,
        'Service': serializers.ServiceSerializer,
        'Seminar': serializers.SeminarSerializer,
        'SeminarCommunication': serializers.SeminarCommunicationSerializer,
        'Valorisation': serializers.ValorisationSerializer,
        'Course': serializers.CourseSerializer,
        'Paper': serializers.PaperSerializer,
        'UclCourse': serializers.UclCourseSerializer,
    },
    resource_type_field_name='object_type',
)

DoctoralTrainingManyActivitiesSerializerScheme = PolymorphicProxySerializer(
    component_name='DoctoralTrainingActivity',
    serializers={
        'Conference': serializers.ConferenceSerializer,
        'ConferenceCommunication': serializers.ConferenceCommunicationSerializer,
        'ConferencePublication': serializers.ConferencePublicationSerializer,
        'Residency': serializers.ResidencySerializer,
        'ResidencyCommunication': serializers.ResidencyCommunicationSerializer,
        'Communication': serializers.CommunicationSerializer,
        'Publication': serializers.PublicationSerializer,
        'Service': serializers.ServiceSerializer,
        'Seminar': serializers.SeminarSerializer,
        'SeminarCommunication': serializers.SeminarCommunicationSerializer,
        'Valorisation': serializers.ValorisationSerializer,
        'Course': serializers.CourseSerializer,
        'Paper': serializers.PaperSerializer,
        'UclCourse': serializers.UclCourseSerializer,
    },
    resource_type_field_name='object_type',
    many=True,
)


class DoctoralTrainingListView(DoctorateAPIPermissionRequiredMixin, GenericAPIView):
    name = "doctoral-training"
    pagination_class = None
    filter_backends = []
    serializer_class = DoctoralTrainingActivitySerializer
    lookup_field = 'uuid'
    lookup_url_kwarg = 'activity_id'
    permission_mapping = {
        'GET': 'parcours_doctoral.view_doctoral_training',
        'POST': 'parcours_doctoral.add_training',
    }

    def get_queryset(self):
        return Activity.objects.for_doctoral_training(self.doctorate_uuid)

    @extend_schema(
        responses=DoctoralTrainingManyActivitiesSerializerScheme,
        operation_id='list_doctoral_training',
    )
    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    @extend_schema(
        request=DoctoralTrainingActivitySerializerScheme,
        responses=DoctoralTrainingActivitySerializerScheme,
        operation_id='create_doctoral_training',
    )
    def post(self, request, *args, **kwargs):
        doctorate = self.get_permission_object()
        data = {
            **request.data,
            'parcours_doctoral': doctorate.pk,
        }
        serializer = DoctoralTrainingActivitySerializer(parcours_doctoral=doctorate, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TrainingConfigView(DoctorateAPIPermissionRequiredMixin, RetrieveModelMixin, GenericAPIView):
    name = "training-config"
    pagination_class = None
    filter_backends = []
    serializer_class = DoctoralTrainingConfigSerializer
    lookup_field = 'uuid'
    permission_mapping = {
        'GET': 'parcours_doctoral.view_training',
    }

    def get_object(self):
        management_entity_id = self.get_permission_object().training.management_entity_id
        return CddConfiguration.objects.get_or_create(cdd_id=management_entity_id)[0]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['doctorate'] = self.get_permission_object() if self.doctorate_uuid else None
        return context

    @extend_schema(operation_id='retrieve_doctoral_training_config')
    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)


class TrainingView(DoctorateAPIPermissionRequiredMixin, GenericAPIView):
    name = "training"
    pagination_class = None
    filter_backends = []
    serializer_class = DoctoralTrainingActivitySerializer
    lookup_field = 'uuid'
    lookup_url_kwarg = 'activity_id'
    permission_mapping = {
        'GET': 'parcours_doctoral.view_training',
        'PUT': 'parcours_doctoral.update_training',
        'DELETE': 'parcours_doctoral.delete_training',
    }

    def get_queryset(self):
        return (
            Activity.objects.filter(parcours_doctoral__uuid=self.doctorate_uuid)
            .prefetch_related('children')
            .select_related('learning_unit_year')
        )

    @extend_schema(
        responses=DoctoralTrainingActivitySerializerScheme,
        operation_id='retrieve_training',
    )
    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = DoctoralTrainingActivitySerializer(instance, parcours_doctoral=self.get_permission_object())
        return Response(serializer.data)

    @extend_schema(
        request=DoctoralTrainingActivitySerializerScheme,
        responses=DoctoralTrainingActivitySerializerScheme,
        operation_id='update_training',
    )
    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        data = {
            **request.data,
            'parcours_doctoral': self.get_permission_object().pk,
        }
        serializer = DoctoralTrainingActivitySerializer(
            instance, parcours_doctoral=self.get_permission_object(), data=data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(operation_id='destroy_training')
    def delete(self, request, *args, **kwargs):
        message_bus_instance.invoke(SupprimerActiviteCommand(activite_uuid=str(kwargs["activity_id"])))
        return Response(status=status.HTTP_204_NO_CONTENT)


class TrainingSubmitView(DoctorateAPIPermissionRequiredMixin, GenericAPIView):
    name = "training-submit"
    pagination_class = None
    filter_backends = []
    serializer_class = DoctoralTrainingBatchSerializer
    lookup_field = 'uuid'
    permission_mapping = {
        'POST': 'parcours_doctoral.submit_training',
    }

    @extend_schema(
        operation_id='submit_training',
    )
    def post(self, request, *args, **kwargs):
        """Submit doctoral training activities."""
        serializer = DoctoralTrainingBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cmd = SoumettreActivitesCommand(
            parcours_doctoral_uuid=self.doctorate_uuid,
            activite_uuids=serializer.data['activity_uuids'],
        )
        try:
            message_bus_instance.invoke(cmd)
        except MultipleBusinessExceptions as exc:
            # Bypass normal exception handling to add activity_id to each error
            data = {
                api_settings.NON_FIELD_ERRORS_KEY: [
                    {
                        "status_code": exception.status_code,
                        "detail": exception.message,
                        "activite_id": str(exception.activite_id.uuid),
                    }
                    for exception in exc.exceptions
                ]
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TrainingAssentView(DoctorateAPIPermissionRequiredMixin, GenericAPIView):
    name = "training-assent"
    pagination_class = None
    filter_backends = []
    serializer_class = DoctoralTrainingAssentSerializer
    lookup_field = 'uuid'
    permission_mapping = {
        'POST': 'parcours_doctoral.assent_training',
    }

    @extend_schema(
        parameters=[
            DoctoralTrainingAssentSerializer,
            OpenApiParameter(
                name='activity_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
            ),
        ],
        operation_id='assent_training',
    )
    def post(self, request, *args, **kwargs):
        """Assent on a doctoral training activity."""
        serializer = DoctoralTrainingAssentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cmd = DonnerAvisSurActiviteCommand(
            parcours_doctoral_uuid=self.doctorate_uuid,
            activite_uuid=self.request.GET['activity_id'],
            **serializer.data,
        )
        message_bus_instance.invoke(cmd)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        responses=DoctoralTrainingManyActivitiesSerializerScheme,
        operation_id='list_complementary_training',
    ),
)
class ComplementaryTrainingListView(DoctoralTrainingListView):
    name = "complementary-training"
    http_method_names = ['get']
    permission_mapping = {
        'GET': 'parcours_doctoral.view_complementary_training',
    }

    def get_queryset(self):
        return Activity.objects.for_complementary_training(self.doctorate_uuid)


@extend_schema_view(
    get=extend_schema(
        responses=DoctoralTrainingManyActivitiesSerializerScheme,
        operation_id='list_course_enrollment',
    ),
)
class CourseEnrollmentListView(DoctoralTrainingListView):
    name = "course-enrollment"
    http_method_names = ['get']
    permission_mapping = {
        'GET': 'parcours_doctoral.view_course_enrollment',
    }

    def get_queryset(self):
        return Activity.objects.for_enrollment_courses(self.doctorate_uuid)


@extend_schema_view(
    get=extend_schema(
        responses=serializers.InscriptionEvaluationDTOSerializer,
        operation_id='list_inscription_evaluation_dtos',
    ),
)
class AssessmentEnrollmentListView(DoctorateAPIPermissionRequiredMixin, ListAPIView):
    name = "assessment-enrollment-list"
    http_method_names = ['get']
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.view_assessment_enrollment',
    }
    serializer_class = InscriptionEvaluationDTOSerializer

    def get_queryset(self):
        return message_bus_instance.invoke(
            RecupererInscriptionsEvaluationsQuery(
                parcours_doctoral_uuid=self.doctorate_uuid,
            )
        )


@extend_schema_view(
    get=extend_schema(
        responses=serializers.InscriptionEvaluationDTOSerializer,
        operation_id='retrieve_inscription_evaluation_dto',
    ),
)
class AssessmentEnrollmentDetailView(DoctorateAPIPermissionRequiredMixin, RetrieveAPIView):
    name = "assessment-enrollment-detail"
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.view_assessment_enrollment',
    }
    serializer_class = InscriptionEvaluationDTOSerializer

    def get_object(self):
        return message_bus_instance.invoke(
            RecupererInscriptionEvaluationQuery(
                inscription_uuid=self.kwargs['enrollment_uuid'],
            )
        )


class TrainingRecapPdfApiView(DoctorateAPIPermissionRequiredMixin, RetrieveModelMixin, GenericAPIView):
    name = "training-pdf-recap"
    http_method_names = ['get']
    permission_mapping = {
        'GET': 'parcours_doctoral.view_doctoral_training',
    }
    pagination_class = None
    filter_backends = []

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['activities'] = Activity.objects.for_doctoral_training(self.doctorate_uuid).filter(
            status=StatutActivite.ACCEPTEE.name
        )
        return context

    @extend_schema(
        request=TrainingRecapPdfSerializer,
        responses=TrainingRecapPdfSerializer,
        operation_id='training_recap_pdf',
    )
    def get(self, request, *args, **kwargs):
        """Get the recap PDF of the doctoral training"""
        doctorate_object = self.get_permission_object()

        doctorate_dto = message_bus_instance.invoke(
            RecupererParcoursDoctoralQuery(parcours_doctoral_uuid=self.doctorate_uuid),
        )

        url = parcours_doctoral_pdf_formation_doctorale(
            parcours_doctoral=doctorate_dto,
            context=self.get_serializer_context(),
            language=doctorate_object.student.language,
        )

        serializer = TrainingRecapPdfSerializer(data={'url': url})
        serializer.is_valid()
        return Response(data=serializer.data)
