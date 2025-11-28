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

import attr

from base.ddd.utils.business_validator import BusinessValidator
from parcours_doctoral.ddd.defense_privee_soutenance_publique.validators.exceptions import (
    EtapeDefensePriveeEtSoutenancePubliquePasEnCoursException,
    StatutDoctoratDifferentDefensePriveeEtSoutenancePubliqueAutoriseesException,
    StatutDoctoratDifferentDefensePriveeEtSoutenancePubliqueSoumisesException,
)
from parcours_doctoral.ddd.domain.model.enums import (
    STATUTS_DOCTORAT_DEFENSE_PRIVEE_SOUTENANCE_PUBLIQUE_EN_COURS,
    ChoixStatutParcoursDoctoral,
)

__all__ = [
    'ShouldEtapeDefensePriveeEtSoutenancePubliqueEtreEnCours',
    'ShouldStatutDoctoratEtreDefensePriveeEtSoutenancePubliqueSoumises',
    'ShouldStatutDoctoratEtreDefensePriveeEtSoutenancePubliqueAutorisees',
]


@attr.dataclass(frozen=True, slots=True)
class ShouldEtapeDefensePriveeEtSoutenancePubliqueEtreEnCours(BusinessValidator):
    statut: ChoixStatutParcoursDoctoral

    def validate(self, *args, **kwargs):
        if self.statut.name not in STATUTS_DOCTORAT_DEFENSE_PRIVEE_SOUTENANCE_PUBLIQUE_EN_COURS:
            raise EtapeDefensePriveeEtSoutenancePubliquePasEnCoursException


@attr.dataclass(frozen=True, slots=True)
class ShouldStatutDoctoratEtreDefensePriveeEtSoutenancePubliqueSoumises(BusinessValidator):
    statut: ChoixStatutParcoursDoctoral

    def validate(self, *args, **kwargs):
        if self.statut != ChoixStatutParcoursDoctoral.DEFENSE_ET_SOUTENANCE_SOUMISES:
            raise StatutDoctoratDifferentDefensePriveeEtSoutenancePubliqueSoumisesException


@attr.dataclass(frozen=True, slots=True)
class ShouldStatutDoctoratEtreDefensePriveeEtSoutenancePubliqueAutorisees(BusinessValidator):
    statut: ChoixStatutParcoursDoctoral

    def validate(self, *args, **kwargs):
        if self.statut != ChoixStatutParcoursDoctoral.DEFENSE_ET_SOUTENANCE_AUTORISEES:
            raise StatutDoctoratDifferentDefensePriveeEtSoutenancePubliqueAutoriseesException
