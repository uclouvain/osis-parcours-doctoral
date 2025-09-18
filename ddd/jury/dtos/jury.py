##############################################################################
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
##############################################################################
import datetime
from typing import List, Optional

import attr

from osis_common.ddd import interface
from parcours_doctoral.constants import INSTITUTION_UCL


@attr.dataclass(frozen=True, slots=True)
class SignatureMembreJuryDTO(interface.DTO):
    etat: str
    date: Optional[datetime.datetime]
    commentaire_externe: str
    commentaire_interne: str
    motif_refus: str
    pdf: List[str]


@attr.dataclass(frozen=True, slots=True)
class MembreJuryDTO(interface.DTO):
    uuid: str
    role: str
    est_promoteur: bool
    est_promoteur_de_reference: bool
    matricule: str
    institution: str
    autre_institution: str
    pays: str
    nom: str
    prenom: str
    titre: str
    justification_non_docteur: str
    genre: str
    langue: str
    email: str
    signature: SignatureMembreJuryDTO
    ville: str

    def membre_ucl(self):
        return self.institution == INSTITUTION_UCL


@attr.dataclass(frozen=True, slots=True)
class JuryDTO(interface.DTO):
    uuid: str
    titre_propose: str

    membres: List[MembreJuryDTO]

    formule_defense: str
    date_indicative: str
    nom_langue_redaction: str
    langue_redaction: str
    nom_langue_soutenance: str
    langue_soutenance: str
    commentaire: str
    situation_comptable: Optional[bool]
    approbation_pdf: List[str]


@attr.dataclass(frozen=True, slots=True)
class AvisDTO(interface.DTO):
    etat: str
    commentaire_externe: Optional[str] = ''
    commentaire_interne: Optional[str] = ''
    motif_refus: Optional[str] = ''
    pdf: List[str] = attr.Factory(list)
