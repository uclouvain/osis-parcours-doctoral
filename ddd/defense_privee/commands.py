# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
import datetime
from typing import List, Optional

import attr

from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class RecupererDefensesPriveesQuery(interface.QueryRequest):
    parcours_doctoral_uuid: str


@attr.dataclass(frozen=True, slots=True)
class RecupererDerniereDefensePriveeQuery(interface.QueryRequest):
    parcours_doctoral_uuid: str


@attr.dataclass(frozen=True, slots=True)
class RecupererDefensePriveeQuery(interface.QueryRequest):
    uuid: str


@attr.dataclass(frozen=True, slots=True)
class SoumettreDefensePriveeCommand(interface.CommandRequest):
    uuid: str
    matricule_auteur: str

    titre_these: str
    date_heure: datetime.datetime
    lieu: Optional[str]
    date_envoi_manuscrit: Optional[datetime.date]


@attr.dataclass(frozen=True, slots=True)
class ModifierDefensePriveeCommand(interface.CommandRequest):
    uuid: str
    matricule_auteur: str

    titre_these: str
    date_heure: datetime.datetime
    lieu: Optional[str]
    date_envoi_manuscrit: Optional[datetime.date]
    proces_verbal: list[str]


@attr.dataclass(frozen=True, slots=True)
class AutoriserDefensePriveeCommand(interface.CommandRequest):
    parcours_doctoral_uuid: str

    matricule_auteur: str
    sujet_message: str
    corps_message: str


@attr.dataclass(frozen=True, slots=True)
class InviterJuryDefensePriveeCommand(interface.CommandRequest):
    parcours_doctoral_uuid: str
    matricule_auteur: str


@attr.dataclass(frozen=True, slots=True)
class SoumettreProcesVerbalDefensePriveeCommand(interface.CommandRequest):
    uuid: str
    matricule_auteur: str

    proces_verbal: list[str]


@attr.dataclass(frozen=True, slots=True)
class ConfirmerReussiteDefensePriveeCommand(interface.CommandRequest):
    parcours_doctoral_uuid: str

    matricule_auteur: str
    sujet_message: str
    corps_message: str


@attr.dataclass(frozen=True, slots=True)
class ConfirmerEchecDefensePriveeCommand(interface.CommandRequest):
    parcours_doctoral_uuid: str

    matricule_auteur: str
    sujet_message: str
    corps_message: str


@attr.dataclass(frozen=True, slots=True)
class ConfirmerDefensePriveeARecommencerCommand(interface.CommandRequest):
    parcours_doctoral_uuid: str

    matricule_auteur: str
    sujet_message: str
    corps_message: str
