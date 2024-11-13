# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Optional

import attr

from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class RecupererParcoursDoctoralQuery(interface.QueryRequest):
    parcours_doctoral_uuid: str


@attr.dataclass(frozen=True, slots=True)
class InitialiserParcoursDoctoralCommand(interface.CommandRequest):
    proposition_uuid: str


@attr.dataclass(frozen=True, slots=True)
class EnvoyerMessageDoctorantCommand(interface.CommandRequest):
    matricule_emetteur: str
    parcours_doctoral_uuid: str
    sujet: str
    message: str
    cc_promoteurs: bool
    cc_membres_ca: bool


@attr.dataclass(frozen=True, slots=True)
class GetGroupeDeSupervisionCommand(interface.QueryRequest):
    uuid_parcours_doctoral: str


@attr.dataclass(frozen=True, slots=True)
class IdentifierPromoteurCommand(interface.CommandRequest):
    uuid_parcours_doctoral: str
    matricule_auteur: str
    matricule: Optional[str]
    prenom: Optional[str]
    nom: Optional[str]
    email: Optional[str]
    est_docteur: Optional[bool]
    institution: Optional[str]
    ville: Optional[str]
    pays: Optional[str]
    langue: Optional[str]


@attr.dataclass(frozen=True, slots=True)
class IdentifierMembreCACommand(interface.CommandRequest):
    uuid_parcours_doctoral: str
    matricule_auteur: str
    matricule: Optional[str]
    prenom: Optional[str]
    nom: Optional[str]
    email: Optional[str]
    est_docteur: Optional[bool]
    institution: Optional[str]
    ville: Optional[str]
    pays: Optional[str]
    langue: Optional[str]


@attr.dataclass(frozen=True, slots=True)
class ModifierMembreSupervisionExterneCommand(interface.CommandRequest):
    uuid_parcours_doctoral: str
    matricule_auteur: str
    uuid_membre: str
    prenom: Optional[str]
    nom: Optional[str]
    email: Optional[str]
    est_docteur: Optional[bool]
    institution: Optional[str]
    ville: Optional[str]
    pays: Optional[str]
    langue: Optional[str]


@attr.dataclass(frozen=True, slots=True)
class DemanderSignaturesCommand(interface.CommandRequest):
    uuid_parcours_doctoral: str
    matricule_auteur: str


@attr.dataclass(frozen=True, slots=True)
class RenvoyerInvitationSignatureExterneCommand(interface.CommandRequest):
    uuid_parcours_doctoral: str
    uuid_membre: str

@attr.dataclass(frozen=True, slots=True)
class DesignerPromoteurReferenceCommand(interface.CommandRequest):
    uuid_parcours_doctoral: str
    uuid_promoteur: str
    matricule_auteur: str


@attr.dataclass(frozen=True, slots=True)
class SupprimerMembreCACommand(interface.CommandRequest):
    uuid_parcours_doctoral: str
    uuid_membre_ca: str
    matricule_auteur: str


@attr.dataclass(frozen=True, slots=True)
class SupprimerPromoteurCommand(interface.CommandRequest):
    uuid_parcours_doctoral: str
    uuid_promoteur: str
    matricule_auteur: str

