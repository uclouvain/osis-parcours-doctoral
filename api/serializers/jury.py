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
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from base.utils.serializers import DTOSerializer
from parcours_doctoral.api.serializers.external import (
    ExternalParcoursDoctoralDTOSerializer,
)
from parcours_doctoral.ddd.jury.commands import (
    AjouterMembreCommand,
    ApprouverJuryCommand,
    ApprouverJuryParPdfCommand,
    ModifierJuryCommand,
    ModifierMembreCommand,
    ModifierRoleMembreCommand,
    RefuserJuryCommand,
    RenvoyerInvitationSignatureCommand,
)
from parcours_doctoral.ddd.jury.dtos.jury import JuryDTO, MembreJuryDTO

__all__ = [
    'JuryDTOSerializer',
    'JuryIdentityDTOSerializer',
    'MembreJuryDTOSerializer',
    'MembreJuryIdentityDTOSerializer',
    'ModifierJuryCommandSerializer',
    'AjouterMembreCommandSerializer',
    'ModifierMembreCommandSerializer',
    'ModifierRoleMembreCommandSerializer',
]


class JuryDTOSerializer(DTOSerializer):
    has_change_roles_permission = serializers.SerializerMethodField()

    class Meta:
        source = JuryDTO

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_has_change_roles_permission(self, obj):
        return self.context['request'].user.has_perm(
            'parcours_doctoral.api_change_jury_role', self.context['parcours_doctoral']
        )


class JuryIdentityDTOSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(read_only=True)


class MembreJuryDTOSerializer(DTOSerializer):
    class Meta:
        source = MembreJuryDTO


class MembreJuryIdentityDTOSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(read_only=True)


class ModifierJuryCommandSerializer(DTOSerializer):
    uuid_parcours_doctoral = None

    class Meta:
        source = ModifierJuryCommand


class AjouterMembreCommandSerializer(DTOSerializer):
    uuid_jury = None

    class Meta:
        source = AjouterMembreCommand


class ModifierMembreCommandSerializer(DTOSerializer):
    uuid_jury = None
    uuid_membre = None

    class Meta:
        source = ModifierMembreCommand


class ModifierRoleMembreCommandSerializer(DTOSerializer):
    uuid_jury = None
    uuid_membre = None
    matricule_auteur = None

    class Meta:
        source = ModifierRoleMembreCommand


class ExternalJuryDTOSerializer(serializers.Serializer):
    parcours_doctoral = ExternalParcoursDoctoralDTOSerializer()
    jury = JuryDTOSerializer()


class RenvoyerInvitationSignatureExterneSerializer(DTOSerializer):
    uuid_jury = None

    class Meta:
        source = RenvoyerInvitationSignatureCommand


class ApprouverJuryCommandSerializer(DTOSerializer):
    uuid_jury = None

    class Meta:
        source = ApprouverJuryCommand


class RefuserJuryCommandSerializer(DTOSerializer):
    uuid_jury = None

    class Meta:
        source = RefuserJuryCommand


class ApprouverJuryParPdfCommandSerializer(DTOSerializer):
    uuid_jury = None
    matricule_auteur = None

    class Meta:
        source = ApprouverJuryParPdfCommand
