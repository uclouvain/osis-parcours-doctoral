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
from typing import List, Optional
from uuid import UUID

import attr

from osis_common.ddd import interface
from parcours_doctoral.ddd.domain.model.enums import CHOIX_COMMISSION_PROXIMITE
from parcours_doctoral.ddd.dtos.bourse import BourseDTO
from parcours_doctoral.ddd.dtos.formation import FormationDTO


@attr.dataclass(frozen=True, slots=True)
class FinancementDTO(interface.DTO):
    type: str
    type_contrat_travail: str
    eft: Optional[int]
    bourse_recherche: Optional[BourseDTO]
    autre_bourse_recherche: str
    bourse_date_debut: Optional[datetime.date]
    bourse_date_fin: Optional[datetime.date]
    bourse_preuve: List[str]
    duree_prevue: Optional[int]
    temps_consacre: Optional[int]
    est_lie_fnrs_fria_fresh_csc: Optional[bool]
    commentaire: str


@attr.dataclass(frozen=True, slots=True)
class CotutelleDTO(interface.DTO):
    cotutelle: Optional[bool]
    motivation: str
    institution_fwb: Optional[bool]
    institution: str
    autre_institution: Optional[bool]
    autre_institution_nom: str
    autre_institution_adresse: str
    demande_ouverture: List[str]
    convention: List[str]
    autres_documents: List[str]


@attr.dataclass(frozen=True, slots=True)
class ProjetDTO(interface.DTO):
    titre: str
    resume: str
    langue_redaction_these: str
    nom_langue_redaction_these: str
    institut_these: Optional[UUID]
    nom_institut_these: str
    sigle_institut_these: str
    lieu_these: str
    projet_doctoral_deja_commence: Optional[bool]
    projet_doctoral_institution: str
    projet_doctoral_date_debut: Optional[datetime.date]
    documents_projet: List[str]
    graphe_gantt: List[str]
    proposition_programme_doctoral: List[str]
    projet_formation_complementaire: List[str]
    lettres_recommandation: List[str]
    doctorat_deja_realise: str
    institution: str
    domaine_these: str
    date_soutenance: Optional[datetime.date]
    raison_non_soutenue: str


@attr.dataclass(slots=True)
class ParcoursDoctoralDTO(interface.DTO):
    uuid: str
    uuid_admission: str
    reference: str
    statut: str
    date_changement_statut: Optional[datetime.datetime]

    cree_le: datetime.datetime

    formation: FormationDTO

    projet: ProjetDTO
    cotutelle: CotutelleDTO
    financement: FinancementDTO

    photo_identite_doctorant: List[str]
    matricule_doctorant: str
    noma_doctorant: str
    genre_doctorant: str
    prenom_doctorant: str
    nom_doctorant: str
    commission_proximite: str

    @property
    def commission_proximite_display(self):
        return CHOIX_COMMISSION_PROXIMITE.get(self.commission_proximite, '')


@attr.dataclass(slots=True)
class ParcoursDoctoralRechercheEtudiantDTO(interface.DTO):
    uuid: str
    reference: str
    statut: str

    formation: FormationDTO

    matricule_doctorant: str
    genre_doctorant: str
    prenom_doctorant: str
    nom_doctorant: str

    cree_le: datetime.datetime
