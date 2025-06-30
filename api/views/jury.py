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
from rest_framework.views import APIView

from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin
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
from parcours_doctoral.ddd.jury.commands import (
    AjouterMembreCommand,
    ModifierJuryCommand,
    ModifierMembreCommand,
    ModifierRoleMembreCommand,
    RecupererJuryMembreQuery,
    RecupererJuryQuery,
    RetirerMembreCommand, DemanderSignaturesCommand,
)

__all__ = [
    "JuryPreparationAPIView",
    "JuryMembersListAPIView",
    "JuryMemberDetailAPIView",
    "JuryRequestSignaturesAPIView",
]


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
        'GET': 'parcours_doctoral.view_jury',
        'POST': 'parcours_doctoral.change_jury',
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
        'GET': 'parcours_doctoral.view_jury',
        'POST': 'parcours_doctoral.change_jury',
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
        'GET': 'parcours_doctoral.view_jury',
        'PUT': 'parcours_doctoral.change_jury',
        'PATCH': 'parcours_doctoral.change_jury',
        'DELETE': 'parcours_doctoral.change_jury',
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
        'PUT': 'parcours_doctoral.resend_external_invitation',
        'POST': 'parcours_doctoral.request_signatures',
    }

    # @extend_schema(
    #     request=serializers.RenvoyerInvitationSignatureExterneSerializer,
    #     responses=JuryIdentityDTOSerializer,
    #     operation_id='update_signatures',
    # )
    # def put(self, request, *args, **kwargs):
    #     """Resend an invitation for and external member."""
    #     serializer = serializers.RenvoyerInvitationSignatureExterneSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     result = message_bus_instance.invoke(
    #         RenvoyerInvitationSignatureExterneCommand(uuid_proposition=str(kwargs["uuid"]), **serializer.data)
    #     )
    #     serializer = JuryIdentityDTOSerializer(instance=result)
    #     return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=None,
        responses=JuryIdentityDTOSerializer,
        operation_id='create_signatures',
    )
    def post(self, request, *args, **kwargs):
        """Ask for all promoters and members to sign the proposition."""
        result = message_bus_instance.invoke(
            DemanderSignaturesCommand(
                matricule_auteur=self.get_permission_object().candidate.global_id,
                uuid_parcours_doctoral=str(kwargs["uuid"]),
            )
        )
        self.get_permission_object().update_detailed_status(request.user.person)
        serializer = JuryIdentityDTOSerializer(instance=result)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# EXTERNAL_ACTOR_TOKEN_EXPIRATION_DAYS = 7
#
#
# class ApprovePropositionMixin:
#     def get_permission_object(self):
#         return get_cached_admission_perm_obj(self.kwargs['uuid'])
#
#     def post(self, request, *args, **kwargs):
#         """Approve the proposition."""
#         serializer = serializers.ApprouverPropositionCommandSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#
#         proposition_id = message_bus_instance.invoke(
#             ApprouverPropositionCommand(
#                 uuid_proposition=str(kwargs["uuid"]),
#                 **serializer.data,
#             ),
#         )
#         self.get_permission_object().update_detailed_status(getattr(request.user, 'person', None))
#
#         serializer = serializers.PropositionIdentityDTOSerializer(instance=proposition_id)
#         return Response(serializer.data, status=status.HTTP_200_OK)
#
#     def put(self, request, *args, **kwargs):
#         """Reject the proposition."""
#         serializer = serializers.RefuserPropositionCommandSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#
#         proposition_id = message_bus_instance.invoke(
#             RefuserPropositionCommand(
#                 uuid_proposition=str(kwargs["uuid"]),
#                 **serializer.data,
#             ),
#         )
#         self.get_permission_object().update_detailed_status(getattr(request.user, 'person', None))
#
#         serializer = serializers.PropositionIdentityDTOSerializer(instance=proposition_id)
#         return Response(serializer.data, status=status.HTTP_200_OK)
#
#
# @extend_schema_view(
#     post=extend_schema(
#         request=serializers.ApprouverPropositionCommandSerializer,
#         responses=serializers.PropositionIdentityDTOSerializer,
#         operation_id='approve_proposition',
#     ),
#     put=extend_schema(
#         request=serializers.RefuserPropositionCommandSerializer,
#         responses=serializers.PropositionIdentityDTOSerializer,
#         operation_id='reject_proposition',
#     ),
# )
# class ApprovePropositionAPIView(ApprovePropositionMixin, APIPermissionRequiredMixin, APIView):
#     name = "approvals"
#     permission_mapping = {
#         'POST': 'admission.approve_proposition',
#         'PUT': 'admission.approve_proposition',
#     }
#
#
# @extend_schema_view(
#     get=extend_schema(
#         responses=serializers.ExternalSupervisionDTOSerializer,
#         operation_id='get_external_proposition',
#     ),
#     post=extend_schema(
#         request=serializers.ApprouverPropositionCommandSerializer,
#         responses=serializers.PropositionIdentityDTOSerializer,
#         operation_id='approve_external_proposition',
#     ),
#     put=extend_schema(
#         request=serializers.RefuserPropositionCommandSerializer,
#         responses=serializers.PropositionIdentityDTOSerializer,
#         operation_id='reject_external_proposition',
#     ),
# )
# class ExternalApprovalPropositionAPIView(ApprovePropositionMixin, APIView):
#     name = "external-approvals"
#     authentication_classes = []
#     permission_classes = []
#
#     @cached_property
#     def actor(self):
#         return get_actor_from_token(self.kwargs['token'])
#
#     def initial(self, request, *args, **kwargs):
#         super().initial(request, *args, **kwargs)
#         # Load actor from token
#         if (
#             not self.actor
#             # must be part of supervision group
#             or self.actor.process_id != self.get_permission_object().supervision_group_id
#             # must be not older than 7 days
#             or self.actor.states.last().created_at < now() - timedelta(days=EXTERNAL_ACTOR_TOKEN_EXPIRATION_DAYS)
#         ):
#             raise PermissionDenied
#         # Override the request data to use the actor's uuid loaded from token
#         request.data['uuid_membre'] = str(self.actor.uuid)
#
#     def get(self, request, *args, **kwargs):
#         """Returns necessary info about proposition while checking token."""
#         proposition = message_bus_instance.invoke(GetPropositionCommand(uuid_proposition=kwargs.get('uuid')))
#         supervision = message_bus_instance.invoke(GetGroupeDeSupervisionCommand(uuid_proposition=kwargs['uuid']))
#         serializer = serializers.ExternalSupervisionDTOSerializer(
#             instance={
#                 'proposition': proposition,
#                 'supervision': supervision,
#             },
#         )
#         return Response(serializer.data, status=status.HTTP_200_OK)
#
#
# class ApproveByPdfPropositionAPIView(APIPermissionRequiredMixin, APIView):
#     name = "approve-by-pdf"
#     permission_mapping = {
#         'POST': 'admission.approve_proposition_by_pdf',
#     }
#
#     def get_permission_object(self):
#         return get_cached_admission_perm_obj(self.kwargs['uuid'])
#
#     @extend_schema(
#         request=serializers.ApprouverPropositionParPdfCommandSerializer,
#         responses=serializers.PropositionIdentityDTOSerializer,
#         operation_id='approve_by_pdf',
#     )
#     def post(self, request, *args, **kwargs):
#         """Approve the proposition with a pdf file."""
#         serializer = serializers.ApprouverPropositionParPdfCommandSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#
#         proposition_id = message_bus_instance.invoke(
#             ApprouverPropositionParPdfCommand(
#                 uuid_proposition=str(kwargs["uuid"]),
#                 matricule_auteur=self.get_permission_object().candidate.global_id,
#                 **serializer.data,
#             ),
#         )
#         self.get_permission_object().update_detailed_status(request.user.person)
#
#         serializer = serializers.PropositionIdentityDTOSerializer(instance=proposition_id)
#         return Response(serializer.data, status=status.HTTP_200_OK)
