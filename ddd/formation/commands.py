# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List, Optional

import attr

from osis_common.ddd import interface
from osis_common.ddd.interface import CommandRequest


@attr.dataclass(frozen=True, slots=True)
class SupprimerActiviteCommand(CommandRequest):
    activite_uuid: str


@attr.dataclass(frozen=True, slots=True)
class SoumettreActivitesCommand(CommandRequest):
    parcours_doctoral_uuid: str
    activite_uuids: List[str]


@attr.dataclass(frozen=True, slots=True)
class DonnerAvisPositifSurActiviteCommand(CommandRequest):
    parcours_doctoral_uuid: str
    activite_uuid: str
    commentaire: str


@attr.dataclass(frozen=True, slots=True)
class DonnerAvisNegatifSurActiviteCommand(CommandRequest):
    parcours_doctoral_uuid: str
    activite_uuid: str
    commentaire: str


@attr.dataclass(frozen=True, slots=True)
class AccepterActivitesCommand(CommandRequest):
    parcours_doctoral_uuid: str
    activite_uuids: List[str]


@attr.dataclass(frozen=True, slots=True)
class RefuserActiviteCommand(CommandRequest):
    parcours_doctoral_uuid: str
    activite_uuid: str
    avec_modification: bool
    remarque: str


@attr.dataclass(frozen=True, slots=True)
class RevenirSurStatutActiviteCommand(CommandRequest):
    activite_uuid: str


@attr.dataclass(frozen=True, slots=True)
class RecupererInscriptionsEvaluationsQuery(CommandRequest):
    parcours_doctoral_uuid: Optional[str] = None
    cours_uuid: Optional[str] = None


@attr.dataclass(frozen=True, slots=True)
class RecupererInscriptionEvaluationQuery(CommandRequest):
    inscription_uuid: str


@attr.dataclass
class ListerEvaluationsQuery(interface.QueryRequest):
    annee: int
    session: int
    codes_unite_enseignement: List[str]


@attr.dataclass(frozen=True, slots=True)
class InscrireEvaluationCommand(CommandRequest):
    cours_uuid: str
    session: str
    inscription_tardive: bool


@attr.dataclass(frozen=True, slots=True)
class ModifierInscriptionEvaluationCommand(CommandRequest):
    inscription_uuid: str
    session: str
    inscription_tardive: bool


@attr.dataclass(frozen=True, slots=True)
class DesinscrireEvaluationCommand(CommandRequest):
    inscription_uuid: str


@attr.dataclass(frozen=True, slots=True)
class EncoderNoteCommand(CommandRequest):
    annee: int
    session: int
    noma: str
    code_unite_enseignement: str
    note: str


@attr.dataclass
class ListerInscriptionsUnitesEnseignementQuery(interface.QueryRequest):
    annee: int
    code_unite_enseignement: str


@attr.dataclass(frozen=True, slots=True)
class ReinscrireEvaluationCommand(CommandRequest):
    inscription_uuid: str
