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
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from osis_signature.utils import get_actor_from_token
from rest_framework import mixins, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.api.permissions import DoctorateAPIPermissionRequiredMixin
from parcours_doctoral.api.serializers import (
    AjouterMembreCommandSerializer,
    JuryDTOSerializer,
    JuryIdentityDTOSerializer,
    MembreJuryDTOSerializer,
    MembreJuryIdentityDTOSerializer,
    ModifierJuryCommandSerializer,
    ModifierMembreCommandSerializer,
    ModifierRoleMembreCommandSerializer,
)
from parcours_doctoral.api.serializers.jury import (
    ApprouverJuryCommandSerializer,
    ApprouverJuryParPdfCommandSerializer,
    ExternalJuryDTOSerializer,
    RefuserJuryCommandSerializer,
    RenvoyerInvitationSignatureExterneSerializer,
)
from parcours_doctoral.ddd.commands import (
    GenererPdfArchiveCommand,
    RecupererParcoursDoctoralQuery,
)
from parcours_doctoral.ddd.jury.commands import (
    AjouterMembreCommand,
    ApprouverJuryCommand,
    ApprouverJuryParPdfCommand,
    DemanderSignaturesCommand,
    ModifierJuryCommand,
    ModifierMembreCommand,
    ModifierRoleMembreCommand,
    RecupererJuryMembreQuery,
    RecupererJuryQuery,
    RefuserJuryCommand,
    RenvoyerInvitationSignatureCommand,
    RetirerMembreCommand,
    VerifierJuryConditionSignatureQuery,
)
from parcours_doctoral.utils.cache import get_cached_parcours_doctoral_perm_obj
from parcours_doctoral.utils.ddd import gather_business_exceptions

__all__ = [
    "JuryPreparationAPIView",
    "JuryMembersListAPIView",
    "JuryMemberDetailAPIView",
    "JuryRequestSignaturesAPIView",
    "JuryApprovePropositionAPIView",
    "JuryExternalApprovalPropositionAPIView",
    "JuryApproveByPdfPropositionAPIView",
]

EXTERNAL_ACTOR_TOKEN_EXPIRATION_DAYS = 7


class JuryPreparationAPIView(
    DoctorateAPIPermissionRequiredMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericAPIView,
):
    name = "jury-preparation"
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.api_view_jury',
        'POST': 'parcours_doctoral.api_change_jury',
    }

    @extend_schema(
        responses=JuryDTOSerializer,
        operation_id='retrieve_jury_preparation',
    )
    def get(self, request, *args, **kwargs):
        """Get the Jury of a doctorate"""
        jury = message_bus_instance.invoke(RecupererJuryQuery(uuid_jury=self.doctorate_uuid))
        serializer = JuryDTOSerializer(instance=jury)
        return Response(serializer.data)

    @extend_schema(
        request=ModifierJuryCommandSerializer,
        responses=JuryIdentityDTOSerializer,
        operation_id='update_jury_preparation',
    )
    def post(self, request, *args, **kwargs):
        """Update the jury preparation information"""
        serializer = ModifierJuryCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = message_bus_instance.invoke(
            ModifierJuryCommand(
                uuid_parcours_doctoral=str(self.doctorate_uuid),
                **serializer.data,
            )
        )
        serializer = JuryIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)


class JuryMembersListAPIView(
    DoctorateAPIPermissionRequiredMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericAPIView,
):
    name = "jury-members-list"
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.api_view_jury',
        'POST': 'parcours_doctoral.api_change_jury',
    }

    @extend_schema(
        responses=MembreJuryDTOSerializer,
        operation_id='list_jury_members',
    )
    def get(self, request, *args, **kwargs):
        """Get the members of a jury"""
        jury = message_bus_instance.invoke(RecupererJuryQuery(uuid_jury=self.doctorate_uuid))
        serializer = MembreJuryDTOSerializer(instance=jury.membres, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=AjouterMembreCommandSerializer,
        responses=MembreJuryIdentityDTOSerializer,
        operation_id='create_jury_members',
    )
    def post(self, request, *args, **kwargs):
        """Add a new member to the jury"""
        serializer = AjouterMembreCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = message_bus_instance.invoke(
            AjouterMembreCommand(
                uuid_jury=str(self.doctorate_uuid),
                **serializer.data,
            )
        )
        return Response({'uuid': result}, status=status.HTTP_201_CREATED)


class JuryMemberDetailAPIView(
    DoctorateAPIPermissionRequiredMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericAPIView,
):
    name = "jury-member-detail"
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'GET': 'parcours_doctoral.api_view_jury',
        'PUT': 'parcours_doctoral.api_change_jury',
        'PATCH': 'parcours_doctoral.api_change_jury',
        'DELETE': 'parcours_doctoral.api_change_jury',
    }

    @extend_schema(
        responses=MembreJuryDTOSerializer,
        operation_id='retrieve_jury_member',
    )
    def get(self, request, *args, **kwargs):
        """Get the members of a jury"""
        membre = message_bus_instance.invoke(
            RecupererJuryMembreQuery(
                uuid_jury=str(self.doctorate_uuid),
                uuid_membre=str(self.kwargs['member_uuid']),
            )
        )
        serializer = MembreJuryDTOSerializer(instance=membre)
        return Response(serializer.data)

    @extend_schema(
        request=ModifierMembreCommandSerializer,
        responses=JuryIdentityDTOSerializer,
        operation_id='update_jury_member',
    )
    def put(self, request, *args, **kwargs):
        """Update a member of the jury"""
        serializer = ModifierMembreCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = message_bus_instance.invoke(
            ModifierMembreCommand(
                uuid_jury=str(self.doctorate_uuid),
                uuid_membre=str(self.kwargs['member_uuid']),
                **serializer.data,
            )
        )
        serializer = JuryIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=ModifierRoleMembreCommandSerializer,
        responses=JuryIdentityDTOSerializer,
        operation_id='update_role_jury_member',
    )
    def patch(self, request, *args, **kwargs):
        """Update the role of a member of the jury"""
        serializer = ModifierRoleMembreCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = message_bus_instance.invoke(
            ModifierRoleMembreCommand(
                uuid_jury=str(self.doctorate_uuid),
                uuid_membre=str(self.kwargs['member_uuid']),
                **serializer.data,
            )
        )
        serializer = JuryIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=None,
        responses=None,
        operation_id='remove_jury_member',
    )
    def delete(self, request, *args, **kwargs):
        """Remove a member"""
        message_bus_instance.invoke(
            RetirerMembreCommand(
                uuid_jury=str(self.doctorate_uuid),
                uuid_membre=str(self.kwargs['member_uuid']),
            )
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class JuryRequestSignaturesAPIView(DoctorateAPIPermissionRequiredMixin, APIView):
    name = "jury-request-signatures"
    pagination_class = None
    filter_backends = []
    permission_mapping = {
        'PUT': 'parcours_doctoral.api_resend_external_invitation',
        'POST': 'parcours_doctoral.api_request_signatures',
    }

    @extend_schema(
        request=None,
        responses=OpenApiResponse(
            response={
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "status_code": {
                            "type": "string",
                        },
                        "detail": {
                            "type": "string",
                        },
                    },
                },
            },
            description="Project verification errors",
        ),
        operation_id='signature_conditions',
    )
    def get(self, request, *args, **kwargs):
        """Gather the exceptions from signature validation."""
        data = gather_business_exceptions(VerifierJuryConditionSignatureQuery(uuid_jury=str(kwargs["uuid"])))
        return Response(data.get(api_settings.NON_FIELD_ERRORS_KEY, []), status=status.HTTP_200_OK)

    @extend_schema(
        request=RenvoyerInvitationSignatureExterneSerializer,
        responses=JuryIdentityDTOSerializer,
        operation_id='resend_invite',
    )
    def put(self, request, *args, **kwargs):
        """Resend an invitation for an external member."""
        serializer = RenvoyerInvitationSignatureExterneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = message_bus_instance.invoke(
            RenvoyerInvitationSignatureCommand(uuid_jury=str(kwargs["uuid"]), **serializer.data)
        )
        serializer = JuryIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=None,
        responses=JuryIdentityDTOSerializer,
        operation_id='request_signatures',
    )
    def post(self, request, *args, **kwargs):
        """Ask for all promoters and members to sign the jury."""
        message_bus_instance.invoke(
            GenererPdfArchiveCommand(
                auteur=self.get_permission_object().student.global_id,
                uuid_parcours_doctoral=str(kwargs["uuid"]),
            )
        )
        result = message_bus_instance.invoke(
            DemanderSignaturesCommand(
                matricule_auteur=self.get_permission_object().student.global_id,
                uuid_parcours_doctoral=str(kwargs["uuid"]),
            )
        )
        serializer = JuryIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ApprovePropositionMixin:
    def post(self, request, *args, **kwargs):
        """Approve the jury."""
        serializer = ApprouverJuryCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        jury_id = message_bus_instance.invoke(
            ApprouverJuryCommand(
                uuid_jury=str(kwargs["uuid"]),
                **serializer.data,
            ),
        )

        serializer = JuryIdentityDTOSerializer(instance=jury_id)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        """Reject the jury."""
        serializer = RefuserJuryCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        jury_id = message_bus_instance.invoke(
            RefuserJuryCommand(
                uuid_jury=str(kwargs["uuid"]),
                **serializer.data,
            ),
        )

        serializer = JuryIdentityDTOSerializer(instance=jury_id)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    post=extend_schema(
        request=ApprouverJuryCommandSerializer,
        responses=JuryIdentityDTOSerializer,
        operation_id='approve_jury',
    ),
    put=extend_schema(
        request=RefuserJuryCommandSerializer,
        responses=JuryIdentityDTOSerializer,
        operation_id='reject_jury',
    ),
)
class JuryApprovePropositionAPIView(ApprovePropositionMixin, DoctorateAPIPermissionRequiredMixin, APIView):
    name = "jury-approvals"
    permission_mapping = {
        'POST': 'parcours_doctoral.api_approve_jury',
        'PUT': 'parcours_doctoral.api_approve_jury',
    }


@extend_schema_view(
    get=extend_schema(
        responses=ExternalJuryDTOSerializer,
        operation_id='get_external_jury',
    ),
    post=extend_schema(
        request=ApprouverJuryCommandSerializer,
        responses=JuryIdentityDTOSerializer,
        operation_id='approve_external_jury',
    ),
    put=extend_schema(
        request=RefuserJuryCommandSerializer,
        responses=JuryIdentityDTOSerializer,
        operation_id='reject_external_jury',
    ),
)
class JuryExternalApprovalPropositionAPIView(ApprovePropositionMixin, APIView):
    name = "jury-external-approvals"
    authentication_classes = []
    permission_classes = []

    @property
    def doctorate_uuid(self):
        return self.kwargs.get('uuid')

    def get_permission_object(self):
        return get_cached_parcours_doctoral_perm_obj(self.doctorate_uuid)

    @cached_property
    def actor(self):
        return get_actor_from_token(self.kwargs['token'])

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        # Load actor from token
        if (
            not self.actor
            # must be part of supervision group
            or self.actor.process_id != self.get_permission_object().jury_group_id
            # must be not older than 7 days
            or self.actor.states.last().created_at < now() - timedelta(days=EXTERNAL_ACTOR_TOKEN_EXPIRATION_DAYS)
        ):
            raise PermissionDenied
        # Override the request data to use the actor's uuid loaded from token
        request.data['uuid_membre'] = str(self.actor.uuid)

    def get(self, request, *args, **kwargs):
        """Returns necessary info about jury while checking token."""
        parcours_doctoral = message_bus_instance.invoke(
            RecupererParcoursDoctoralQuery(parcours_doctoral_uuid=kwargs.get('uuid'))
        )
        jury = message_bus_instance.invoke(RecupererJuryQuery(uuid_jury=kwargs['uuid']))
        serializer = ExternalJuryDTOSerializer(
            instance={
                'parcours_doctoral': parcours_doctoral,
                'jury': jury,
            },
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class JuryApproveByPdfPropositionAPIView(DoctorateAPIPermissionRequiredMixin, APIView):
    name = "jury-approve-by-pdf"
    permission_mapping = {
        'POST': 'parcours_doctoral.api_approve_jury_by_pdf',
    }

    @extend_schema(
        request=ApprouverJuryParPdfCommandSerializer,
        responses=JuryIdentityDTOSerializer,
        operation_id='approve_by_pdf',
    )
    def post(self, request, *args, **kwargs):
        """Approve the jury with a pdf file."""
        serializer = ApprouverJuryParPdfCommandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        jury_id = message_bus_instance.invoke(
            ApprouverJuryParPdfCommand(
                uuid_jury=str(kwargs["uuid"]),
                matricule_auteur=self.get_permission_object().student.global_id,
                **serializer.data,
            ),
        )

        serializer = JuryIdentityDTOSerializer(instance=jury_id)
        return Response(serializer.data, status=status.HTTP_200_OK)
