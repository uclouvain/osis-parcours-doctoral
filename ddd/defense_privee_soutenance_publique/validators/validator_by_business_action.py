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

from base.ddd.utils.business_validator import (
    BusinessValidator,
    TwoStepsMultipleBusinessExceptionListValidator,
)
from parcours_doctoral.ddd.defense_privee.validators import (
    ShouldDefensePriveeEtreActive,
    ShouldDefensePriveeEtreCompletee,
    ShouldDefensePriveeEtreCompleteePourDecision,
)
from parcours_doctoral.ddd.defense_privee_soutenance_publique.validators import (
    ShouldEtapeDefensePriveeEtSoutenancePubliqueEtreEnCours,
    ShouldStatutDoctoratEtreDefensePriveeEtSoutenancePubliqueAutorisees,
    ShouldStatutDoctoratEtreDefensePriveeEtSoutenancePubliqueSoumises,
)
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.soutenance_publique.validators import *


@attr.dataclass(frozen=True, slots=True)
class SoumettreDefensePriveeEtSoutenancePubliqueFormule2ValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    titre_these: str
    date_heure_defense_privee: Optional[datetime.datetime]

    langue_soutenance_publique: str
    date_heure_soutenance_publique: Optional[datetime.datetime]
    photo_annonce: list[str]

    statut_parcours_doctoral: ChoixStatutParcoursDoctoral

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldDefensePriveeEtreCompletee(
                titre_these=self.titre_these,
                date_heure=self.date_heure_defense_privee,
            ),
            ShouldSoutenancePubliqueEtreCompletee(
                langue_soutenance_publique=self.langue_soutenance_publique,
                date_heure_soutenance_publique=self.date_heure_soutenance_publique,
                photo_annonce=self.photo_annonce,
            ),
            ShouldEtapeDefensePriveeEtSoutenancePubliqueEtreEnCours(
                statut=self.statut_parcours_doctoral,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class AutoriserDefensePriveeEtSoutenancePubliqueValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    statut_parcours_doctoral: ChoixStatutParcoursDoctoral

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldStatutDoctoratEtreDefensePriveeEtSoutenancePubliqueSoumises(
                statut=self.statut_parcours_doctoral,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class InviterJuryDefensePriveeEtSoutenancePubliqueValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    statut_parcours_doctoral: ChoixStatutParcoursDoctoral

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldStatutDoctoratEtreDefensePriveeEtSoutenancePubliqueAutorisees(
                statut=self.statut_parcours_doctoral,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class SoumettreProcesVerbauxDefensePriveeEtSoutenancePubliqueValidatorList(
    TwoStepsMultipleBusinessExceptionListValidator
):
    statut_parcours_doctoral: ChoixStatutParcoursDoctoral

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldStatutDoctoratEtreDefensePriveeEtSoutenancePubliqueAutorisees(
                statut=self.statut_parcours_doctoral,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class DonnerDecisionDefensePriveeEtSoutenancePubliqueValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    statut_parcours_doctoral: ChoixStatutParcoursDoctoral
    proces_verbal_soutenance_publique: list[str]
    date_heure_soutenance_publique: datetime.datetime | None
    defense_privee: 'DefensePrivee'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldDefensePriveeEtreCompleteePourDecision(
                defense_privee=self.defense_privee,
            ),
            ShouldDefensePriveeEtreActive(
                est_active=self.defense_privee.est_active,
            ),
            ShouldSoutenancePubliqueEtreCompleteePourDecision(
                proces_verbal_soutenance_publique=self.proces_verbal_soutenance_publique,
                date_heure_soutenance_publique=self.date_heure_soutenance_publique,
            ),
            ShouldStatutDoctoratEtreDefensePriveeEtSoutenancePubliqueAutorisees(
                statut=self.statut_parcours_doctoral,
            ),
        ]
