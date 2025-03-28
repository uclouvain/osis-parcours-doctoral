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
from typing import List

import attr

from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class RecupererEpreuvesConfirmationQuery(interface.QueryRequest):
    parcours_doctoral_uuid: str


@attr.dataclass(frozen=True, slots=True)
class RecupererDerniereEpreuveConfirmationQuery(interface.QueryRequest):
    parcours_doctoral_uuid: str


@attr.dataclass(frozen=True, slots=True)
class ModifierEpreuveConfirmationParCDDCommand(interface.CommandRequest):
    uuid: str

    date_limite: datetime.date
    date: datetime.date
    rapport_recherche: List[str]

    proces_verbal_ca: List[str]
    avis_renouvellement_mandat_recherche: List[str]


@attr.dataclass(frozen=True, slots=True)
class SoumettreEpreuveConfirmationCommand(interface.CommandRequest):
    uuid: str
    matricule_auteur: str

    date: datetime.date
    rapport_recherche: List[str]

    proces_verbal_ca: List[str]
    avis_renouvellement_mandat_recherche: List[str]


@attr.dataclass(frozen=True, slots=True)
class CompleterEpreuveConfirmationParPromoteurCommand(interface.CommandRequest):
    uuid: str

    proces_verbal_ca: List[str]
    avis_renouvellement_mandat_recherche: List[str]


@attr.dataclass(frozen=True, slots=True)
class SoumettreReportDeDateCommand(interface.CommandRequest):
    uuid: str

    nouvelle_echeance: datetime.date
    justification_succincte: str
    lettre_justification: List[str]


@attr.dataclass(frozen=True, slots=True)
class SoumettreReportDeDateParCDDCommand(interface.CommandRequest):
    uuid: str

    nouvelle_echeance: datetime.date
    justification_succincte: str
    lettre_justification: List[str]


@attr.dataclass(frozen=True, slots=True)
class SoumettreAvisProlongationCommand(interface.CommandRequest):
    uuid: str

    avis_cdd: str


@attr.dataclass(frozen=True, slots=True)
class ConfirmerReussiteCommand(interface.CommandRequest):
    uuid: str
    matricule_auteur: str


@attr.dataclass(frozen=True, slots=True)
class ConfirmerEchecCommand(interface.CommandRequest):
    uuid: str
    matricule_auteur: str

    sujet_message: str
    corps_message: str


@attr.dataclass(frozen=True, slots=True)
class ConfirmerRepassageCommand(interface.CommandRequest):
    uuid: str
    matricule_auteur: str

    date_limite: datetime.date
    sujet_message: str
    corps_message: str


@attr.dataclass(frozen=True, slots=True)
class TeleverserAvisRenouvellementMandatRechercheCommand(interface.CommandRequest):
    uuid: str

    avis_renouvellement_mandat_recherche: List[str]
