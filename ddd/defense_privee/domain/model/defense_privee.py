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
from parcours_doctoral.ddd.defense_privee.validators.validator_by_business_action import (
    SoumettreDefensePriveeValidatorList,
    SoumettreProcesVerbalDefensePriveeValidatorList,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)


@attr.dataclass(frozen=True, slots=True)
class DefensePriveeIdentity(interface.EntityIdentity):
    uuid: str


@attr.dataclass(slots=True, hash=False, eq=False)
class DefensePrivee(interface.RootEntity):
    entity_id: DefensePriveeIdentity

    parcours_doctoral_id: ParcoursDoctoralIdentity

    est_active: bool = True

    date_heure: Optional[datetime.datetime] = None
    lieu: str = ''
    date_envoi_manuscrit: Optional[datetime.date] = None
    proces_verbal: List[str] = attr.Factory(list)
    canevas_proces_verbal: List[str] = attr.Factory(list)

    def soumettre_formulaire(
        self,
        date_heure: datetime.datetime,
        lieu: str,
        date_envoi_manuscrit: Optional[datetime.datetime],
    ):
        self.date_heure = date_heure
        self.lieu = lieu
        self.date_envoi_manuscrit = date_envoi_manuscrit

    def soumettre_proces_verbal(
        self,
        proces_verbal: list[str],
    ):
        SoumettreProcesVerbalDefensePriveeValidatorList(
            est_active=self.est_active,
        ).validate()

        self.proces_verbal = proces_verbal

    def verifier_soumission(
        self,
        titre_these: str,
        date_heure: datetime.datetime,
        est_active: bool,
    ):
        SoumettreDefensePriveeValidatorList(
            titre_these=titre_these,
            date_heure=date_heure,
            est_active=est_active,
        ).validate()
