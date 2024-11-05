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
import datetime
from typing import Optional, List
from uuid import UUID

import attr

from admission.ddd.admission.dtos.bourse import BourseDTO
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class CotutelleDTO(interface.DTO):
    motivation: Optional[str]
    institution_fwb: Optional[bool]
    institution: Optional[str]
    autre_institution: Optional[bool]
    autre_institution_nom: Optional[str]
    autre_institution_adresse: Optional[str]
    demande_ouverture: List[str]
    convention: List[str]
    autres_documents: List[str]


@attr.dataclass(frozen=True, slots=True)
class ProjetDTO(interface.DTO):
    titre: Optional[str]
    resume: Optional[str]
    langue_redaction_these: Optional[str]
    institut_these: Optional[UUID]
    nom_institut_these: str
    sigle_institut_these: str
    lieu_these: str
    projet_doctoral_deja_commence: Optional[bool]
    projet_doctoral_institution: Optional[str]
    projet_doctoral_date_debut: Optional[datetime.date]
    documents_projet: List[str]
    graphe_gantt: List[str]
    proposition_programme_doctoral: List[str]
    projet_formation_complementaire: List[str]
    lettres_recommandation: List[str]
    doctorat_deja_realise: str
    institution: Optional[str]
    domaine_these: str
    date_soutenance: Optional[datetime.date]
    raison_non_soutenue: Optional[str]


@attr.dataclass(frozen=True, slots=True)
class ParcoursDoctoralDTO(interface.DTO):
    uuid: str
    reference: str
    statut: str

    sigle_formation: str
    annee_formation: int
    intitule_formation: str

    projet: ProjetDTO
    cotutelle: Optional[CotutelleDTO]

    titre_these: str
    type_financement: str
    bourse_recherche: Optional[BourseDTO]
    autre_bourse_recherche: Optional[str]

    matricule_doctorant: str
    noma_doctorant: str
    genre_doctorant: str
    prenom_doctorant: str
    nom_doctorant: str
