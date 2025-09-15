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
from typing import Optional

import attr

from deliberation.models.enums.numero_session import Session
from osis_common.ddd import interface
from parcours_doctoral.ddd.formation.domain.model.activite import ActiviteIdentity
from parcours_doctoral.ddd.formation.domain.model.enums import (
    StatutInscriptionEvaluation,
)


@attr.dataclass(frozen=True, slots=True)
class InscriptionEvaluationIdentity(interface.EntityIdentity):
    uuid: str


@attr.dataclass(slots=True, hash=False, eq=False)
class InscriptionEvaluation(interface.RootEntity):
    entity_id: 'InscriptionEvaluationIdentity'
    cours_id: 'ActiviteIdentity'
    statut: StatutInscriptionEvaluation
    session: Session
    inscription_tardive: bool
    desinscription_tardive: bool

    def modifier(
        self,
        session: Session,
        inscription_tardive: bool,
    ):
        self.session = session
        self.inscription_tardive = inscription_tardive

    def desinscrire(self, echeance_encodage_note: Optional[datetime.date]):
        self.statut = StatutInscriptionEvaluation.DESINSCRITE
        self.desinscription_tardive = bool(echeance_encodage_note and datetime.date.today() > echeance_encodage_note)

    def reinscrire(self):
        self.statut = StatutInscriptionEvaluation.ACCEPTEE
