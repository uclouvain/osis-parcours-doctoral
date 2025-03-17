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

from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.settings import api_settings

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.api.permissions import DoctorateAPIPermissionRequiredMixin
from parcours_doctoral.api.schema import (
    AuthorizationAwareSchema,
    AuthorizationAwareSchemaMixin,
    ChoicesEnumSchema,
    ResponseSpecificSchema,
)
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


class TrainingListSchema(ChoicesEnumSchema):
    def get_operation_id_base(self, path: str, method: str, action) -> str:
        return f"_{self.view.name.replace('-', '_')}"

    def map_serializer(self, serializer):
        if isinstance(serializer, DoctoralTrainingActivitySerializer):
            possible_classes = serializer.serializer_class_mapping.values()
            if serializer.only_classes:
                # Only one of specified classes (for children)
                possible_classes = serializer.only_classes
            return {
                'oneOf': [self._get_reference(s()) for s in possible_classes],
                'discriminator': {'propertyName': 'object_type'},
            }
        return super().map_serializer(serializer)

    def get_components(self, path, method):
        components = super().get_components(path, method)
        for mapping_key, serializer in DoctoralTrainingActivitySerializer.serializer_class_mapping.items():
            # Specify the children classes if needed, by looking for parent category in the mapping key
            child_classes = DoctoralTrainingActivitySerializer.get_child_classes(mapping_key)

            serializer_dummy_instance = serializer(child_classes=child_classes)
            component_name = self.get_component_name(serializer_dummy_instance)
            components.setdefault(component_name, self.map_serializer(serializer_dummy_instance))
        return components


class DoctoralTrainingListView(DoctorateAPIPermissionRequiredMixin, GenericAPIView):
    name = "doctoral-training"
    pagination_class = None
    filter_backends = []
    serializer_class = DoctoralTrainingActivitySerializer
    schema = TrainingListSchema()
    lookup_field = 'uuid'
    lookup_url_kwarg = 'activity_id'
    permission_mapping = {
        'GET': 'parcours_doctoral.view_doctoral_training',
        'POST': 'parcours_doctoral.add_training',
    }

    def get_queryset(self):
        return Activity.objects.for_doctoral_training(self.doctorate_uuid)

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

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
    schema = AuthorizationAwareSchema()
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

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)


class TrainingView(DoctorateAPIPermissionRequiredMixin, GenericAPIView):
    name = "training"
    pagination_class = None
    filter_backends = []
    serializer_class = DoctoralTrainingActivitySerializer
    schema = TrainingListSchema()
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

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = DoctoralTrainingActivitySerializer(instance, parcours_doctoral=self.get_permission_object())
        return Response(serializer.data)

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

    def delete(self, request, *args, **kwargs):
        message_bus_instance.invoke(SupprimerActiviteCommand(activite_uuid=str(kwargs["activity_id"])))
        return Response(status=status.HTTP_204_NO_CONTENT)


class TrainingBatchSchema(AuthorizationAwareSchemaMixin, AutoSchema):
    def get_operation_id(self, path, method):
        return "submit_training"


class TrainingSubmitView(DoctorateAPIPermissionRequiredMixin, GenericAPIView):
    name = "training-submit"
    pagination_class = None
    filter_backends = []
    serializer_class = DoctoralTrainingBatchSerializer
    schema = TrainingBatchSchema()
    lookup_field = 'uuid'
    permission_mapping = {
        'POST': 'parcours_doctoral.submit_training',
    }

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


class TrainingAssentSchema(AuthorizationAwareSchemaMixin, AutoSchema):
    def get_operation_id(self, path, method):
        return "assent_training"

    def get_path_parameters(self, path, method):
        return super().get_path_parameters(path, method) + [
            {
                "name": 'activity_id',
                "in": "query",
                "required": True,
                'schema': {'type': 'string'},
            }
        ]


class TrainingAssentView(DoctorateAPIPermissionRequiredMixin, GenericAPIView):
    name = "training-assent"
    pagination_class = None
    filter_backends = []
    serializer_class = DoctoralTrainingAssentSerializer
    schema = TrainingAssentSchema()
    lookup_field = 'uuid'
    permission_mapping = {
        'POST': 'parcours_doctoral.assent_training',
    }

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


class ComplementaryTrainingListView(DoctoralTrainingListView):
    name = "complementary-training"
    http_method_names = ['get']
    permission_mapping = {
        'GET': 'parcours_doctoral.view_complementary_training',
    }

    def get_queryset(self):
        return Activity.objects.for_complementary_training(self.doctorate_uuid)


class CourseEnrollmentListView(DoctoralTrainingListView):
    name = "course-enrollment"
    http_method_names = ['get']
    permission_mapping = {
        'GET': 'parcours_doctoral.view_course_enrollment',
    }

    def get_queryset(self):
        return Activity.objects.for_enrollment_courses(self.doctorate_uuid)


class AssessmentEnrollmentListView(DoctorateAPIPermissionRequiredMixin, ListAPIView):
    name = "assessment-enrollment-list"
    http_method_names = ['get']
    pagination_class = None
    schema = ChoicesEnumSchema()
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


class AssessmentEnrollmentDetailView(DoctorateAPIPermissionRequiredMixin, RetrieveAPIView):
    name = "assessment-enrollment-detail"
    schema = ChoicesEnumSchema()
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


class TrainingRecapPdfSchema(ResponseSpecificSchema):
    def get_operation_id(self, path, method):
        return "training_recap_pdf"

    serializer_mapping = {
        'GET': TrainingRecapPdfSerializer,
    }


class TrainingRecapPdfApiView(DoctorateAPIPermissionRequiredMixin, RetrieveModelMixin, GenericAPIView):
    name = "training-pdf-recap"
    schema = TrainingRecapPdfSchema()
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
