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
from rest_framework import serializers

from base.utils.serializers import DTOSerializer
from parcours_doctoral.api.serializers.mixins import IncludedFieldsMixin
from parcours_doctoral.api.serializers.supervision import SupervisionDTOSerializer
from parcours_doctoral.ddd.dtos import ParcoursDoctoralDTO
from parcours_doctoral.ddd.dtos.parcours_doctoral import ProjetDTO

__all__ = [
    'ExternalSupervisionDTOSerializer',
]


class ExternalProjetDTOSerializer(IncludedFieldsMixin, DTOSerializer):
    class Meta:
        source = ProjetDTO
        fields = [
            'institut_these',
            'institution',
            'domaine_these',
        ]


class ExternalParcoursDoctoralDTOSerializer(IncludedFieldsMixin, DTOSerializer):
    projet = ExternalProjetDTOSerializer()

    class Meta:
        source = ParcoursDoctoralDTO
        fields = [
            'uuid',
            'archive',
            'formation',
            'matricule_doctorant',
            'projet',
            'statut',
        ]


class ExternalSupervisionDTOSerializer(serializers.Serializer):
    parcours_doctoral = ExternalParcoursDoctoralDTOSerializer()
    supervision = SupervisionDTOSerializer()
