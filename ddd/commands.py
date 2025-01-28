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
class RecupererParcoursDoctoralQuery(interface.QueryRequest):
    parcours_doctoral_uuid: str


@attr.dataclass(frozen=True, slots=True)
class GetCotutelleQuery(interface.QueryRequest):
    uuid_parcours_doctoral: str


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
class GetGroupeDeSupervisionQuery(interface.QueryRequest):
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
class ApprouverMembreParPdfCommand(interface.CommandRequest):
    uuid_parcours_doctoral: str
    matricule_auteur: str
    uuid_membre: str
    pdf: List[str] = attr.Factory(list)


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


@attr.dataclass(frozen=True, slots=True)
class ListerParcoursDoctorauxDoctorantQuery(interface.QueryRequest):
    matricule_doctorant: str


@attr.dataclass(frozen=True, slots=True)
class ListerParcoursDoctorauxSupervisesQuery(interface.QueryRequest):
    matricule_membre: str


@attr.dataclass(frozen=True, slots=True)
class ModifierProjetCommand(interface.CommandRequest):
    uuid: str
    matricule_auteur: str
    titre: str
    resume: str
    documents_projet: List[str]
    graphe_gantt: List[str]
    proposition_programme_doctoral: List[str]
    projet_formation_complementaire: List[str]
    lettres_recommandation: List[str]
    langue_redaction_these: str
    institut_these: str
    lieu_these: str
    projet_doctoral_deja_commence: Optional[bool]
    projet_doctoral_institution: str
    projet_doctoral_date_debut: Optional[datetime.date]
    doctorat_deja_realise: str
    institution: str
    domaine_these: str
    date_soutenance: Optional[datetime.date]
    raison_non_soutenue: str


@attr.dataclass(frozen=True, slots=True)
class ModifierFinancementCommand(interface.CommandRequest):
    uuid: str
    matricule_auteur: str
    type: Optional[str]
    type_contrat_travail: Optional[str]
    eft: Optional[int]
    bourse_recherche: Optional[str]
    autre_bourse_recherche: Optional[str]
    bourse_date_debut: Optional[datetime.date]
    bourse_date_fin: Optional[datetime.date]
    bourse_preuve: List[str]
    duree_prevue: Optional[int]
    temps_consacre: Optional[int]
    est_lie_fnrs_fria_fresh_csc: Optional[bool]
    commentaire: Optional[str]


@attr.dataclass(frozen=True, slots=True)
class ModifierCotutelleCommand(interface.CommandRequest):
    uuid_proposition: str
    matricule_auteur: str
    motivation: Optional[str]
    institution_fwb: Optional[bool]
    institution: Optional[str]
    autre_institution_nom: Optional[str]
    autre_institution_adresse: Optional[str]
    demande_ouverture: List[str]
    convention: List[str]
    autres_documents: List[str]


@attr.dataclass(frozen=True, slots=True)
class InitialiserDocumentCommand(interface.CommandRequest):
    uuid_parcours_doctoral: str
    uuids_documents: List[str]
    libelle: str
    type_document: str
    auteur: Optional[str]


@attr.dataclass(frozen=True, slots=True)
class ModifierDocumentCommand(interface.CommandRequest):
    uuid_parcours_doctoral: str
    identifiant: str
    uuids_documents: List[str]
    auteur: str


@attr.dataclass(frozen=True, slots=True)
class SupprimerDocumentCommand(interface.CommandRequest):
    uuid_parcours_doctoral: str
    identifiant: str


@attr.dataclass(frozen=True, slots=True)
class ListerDocumentsQuery(interface.QueryRequest):
    uuid_parcours_doctoral: str


@attr.dataclass(frozen=True, slots=True)
class RecupererDocumentQuery(interface.QueryRequest):
    uuid_parcours_doctoral: str
    identifiant: str
