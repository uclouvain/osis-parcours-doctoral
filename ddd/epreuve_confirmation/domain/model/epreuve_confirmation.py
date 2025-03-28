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
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.epreuve_confirmation.domain.model._demande_prolongation import (
    DemandeProlongation,
)
from parcours_doctoral.ddd.epreuve_confirmation.validators.validator_by_business_action import (
    EncodageDecisionValidatorList,
    SoumettreAvisProlongationValidatorList,
    SoumettreDemandeProlongationValidatorList,
    SoumettreEpreuveConfirmationValidatorList,
)


@attr.dataclass(frozen=True, slots=True)
class EpreuveConfirmationIdentity(interface.EntityIdentity):
    uuid: str


@attr.dataclass(slots=True, hash=False, eq=False)
class EpreuveConfirmation(interface.RootEntity):
    entity_id: EpreuveConfirmationIdentity

    parcours_doctoral_id: ParcoursDoctoralIdentity
    date_limite: datetime.date

    id: int = 0  # Clé de tri

    date: Optional[datetime.date] = None
    rapport_recherche: List[str] = attr.Factory(list)

    est_active: bool = True

    demande_prolongation: Optional['DemandeProlongation'] = None

    proces_verbal_ca: List[str] = attr.Factory(list)
    attestation_reussite: List[str] = attr.Factory(list)
    attestation_echec: List[str] = attr.Factory(list)
    canevas_proces_verbal_ca: List[str] = attr.Factory(list)
    avis_renouvellement_mandat_recherche: List[str] = attr.Factory(list)

    def faire_demande_prolongation(
        self,
        nouvelle_echeance: datetime.date,
        justification_succincte: str,
        lettre_justification: List[str],
    ):
        self.demande_prolongation = DemandeProlongation(
            nouvelle_echeance=nouvelle_echeance,
            justification_succincte=justification_succincte,
            lettre_justification=lettre_justification,
        )

    def completer(
        self,
        date: datetime.date,
        date_limite: datetime.date,
        rapport_recherche: List[str],
        proces_verbal_ca: List[str],
        avis_renouvellement_mandat_recherche: List[str],
    ):
        self.date = date
        self.date_limite = date_limite
        self.rapport_recherche = rapport_recherche
        self.proces_verbal_ca = proces_verbal_ca
        self.avis_renouvellement_mandat_recherche = avis_renouvellement_mandat_recherche

    def modifier(
        self,
        date: datetime.date,
        rapport_recherche: List[str],
        proces_verbal_ca: List[str],
        avis_renouvellement_mandat_recherche: List[str],
    ):
        self.date = date
        self.rapport_recherche = rapport_recherche
        self.proces_verbal_ca = proces_verbal_ca
        self.avis_renouvellement_mandat_recherche = avis_renouvellement_mandat_recherche

    def verifier(
        self,
        date: Optional[datetime.date],
    ):
        SoumettreEpreuveConfirmationValidatorList(
            date=date,
        ).validate()

    def completer_par_promoteur(
        self,
        proces_verbal_ca: List[str],
        avis_renouvellement_mandat_recherche: List[str],
    ):
        self.proces_verbal_ca = proces_verbal_ca
        self.avis_renouvellement_mandat_recherche = avis_renouvellement_mandat_recherche

    def verifier_demande_prolongation(
        self,
        nouvelle_echeance: datetime.date,
        justification_succincte: str,
    ):
        SoumettreDemandeProlongationValidatorList(
            nouvelle_echeance=nouvelle_echeance,
            justification_succincte=justification_succincte,
        ).validate()

    def verifier_avis_prolongation(self, avis_cdd: str):
        SoumettreAvisProlongationValidatorList(
            nouvel_avis_cdd=avis_cdd,
            demande_prolongation=self.demande_prolongation,
        ).validate()

    def soumettre_avis_prolongation(self, avis_cdd: str):
        self.demande_prolongation = attr.evolve(
            self.demande_prolongation,
            avis_cdd=avis_cdd,
        )

    def verifier_pour_encodage_decision(self):
        EncodageDecisionValidatorList(
            date=self.date,
            proces_verbal_ca=self.proces_verbal_ca,
        ).validate()
        self.attestation_reussite = []

    def televerser_demande_renouvellement_bourse(
        self,
        avis_renouvellement_mandat_recherche: List[str],
    ):
        self.avis_renouvellement_mandat_recherche = avis_renouvellement_mandat_recherche

    def archiver(self):
        self.est_active = False
