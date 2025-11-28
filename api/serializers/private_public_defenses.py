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
from django.utils.timezone import get_default_timezone
from rest_framework import serializers

from base.utils.serializers import DTOSerializer
from parcours_doctoral.ddd.defense_privee_soutenance_publique.commands import (
    SoumettreDefensePriveeEtSoutenancePubliqueCommand,
    SoumettreProcesVerbauxDefensePriveeEtSoutenancePubliqueCommand,
)

__all__ = [
    'SubmitPrivatePublicDefensesSerializer',
    'SubmitPrivatePublicDefensesMinutesSerializer',
]


class SubmitPrivatePublicDefensesSerializer(DTOSerializer):
    """Contains the submitted data to complete the private and public defences."""

    uuid_parcours_doctoral = None
    matricule_auteur = None
    date_heure_defense_privee = serializers.DateTimeField(default_timezone=get_default_timezone())
    date_heure_soutenance_publique = serializers.DateTimeField(default_timezone=get_default_timezone())

    class Meta:
        source = SoumettreDefensePriveeEtSoutenancePubliqueCommand


class SubmitPrivatePublicDefensesMinutesSerializer(DTOSerializer):
    """Contains the submitted data to complete the minutes of the private and public defences."""

    uuid_parcours_doctoral = None
    matricule_auteur = None

    class Meta:
        source = SoumettreProcesVerbauxDefensePriveeEtSoutenancePubliqueCommand
