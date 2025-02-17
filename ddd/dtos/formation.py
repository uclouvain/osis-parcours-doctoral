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
from typing import Optional

import attr

from osis_common.ddd import interface
from parcours_doctoral.ddd.dtos.campus import CampusDTO
from parcours_doctoral.utils.formatting import format_address


@attr.dataclass(frozen=True, slots=True)
class EntiteGestionDTO(interface.DTO):
    sigle: str = ''
    intitule: str = ''
    lieu: Optional[str] = ''
    code_postal: Optional[str] = ''
    ville: Optional[str] = ''
    pays: Optional[str] = ''
    nom_pays: Optional[str] = ''
    numero_telephone: Optional[str] = ''
    code_secteur: str = ''
    intitule_secteur: str = ''

    @property
    def adresse_complete(self):
        return format_address(
            street=self.lieu,
            street_number='',
            postal_code=self.code_postal,
            city=self.ville,
            country=self.nom_pays,
        )


@attr.dataclass(frozen=True, slots=True)
class FormationDTO(interface.DTO):
    sigle: str
    code: str
    annee: int
    intitule: str
    intitule_fr: str
    intitule_en: str
    entite_gestion: EntiteGestionDTO
    campus: Optional[CampusDTO]
    type: str

    def __str__(self):
        return f'{self.sigle} - {self.intitule or self.intitule_fr} ({self.campus})'

    @property
    def nom_complet(self):
        return f'{self.sigle} - {self.intitule or self.intitule_fr}'
