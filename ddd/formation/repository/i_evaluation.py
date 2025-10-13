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

import abc
import datetime
from typing import List, Optional, Tuple

from dateutil.relativedelta import relativedelta

from osis_common.ddd import interface
from parcours_doctoral.ddd.formation.domain.model.evaluation import (
    Evaluation,
    EvaluationIdentity,
)
from parcours_doctoral.ddd.formation.domain.model.inscription_evaluation import (
    InscriptionEvaluationIdentity,
)
from parcours_doctoral.ddd.formation.dtos.evaluation import EvaluationDTO


class IEvaluationRepository(interface.AbstractRepository):
    ECHEANCE_NOMBRE_JOURS_AVANT_DEFENSE_PRIVEE = 2

    @classmethod
    @abc.abstractmethod
    def get(cls, entity_id: 'EvaluationIdentity') -> 'Evaluation':  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_dto(cls, inscription_id: 'InscriptionEvaluationIdentity') -> EvaluationDTO:
        raise NotImplementedError

    @classmethod
    def delete(cls, entity_id: 'EvaluationIdentity', **kwargs) -> None:  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def save(cls, entity: 'Evaluation') -> None:  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    def search(cls, **kwargs) -> List[Evaluation]:  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def search_dto(
        cls,
        annee: int,
        session: int,
        codes_unite_enseignement: List[str],
    ) -> List[EvaluationDTO]:  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    def get_echeance_encodage_enseignant(
        cls,
        date_defense_privee: Optional[datetime.date],
        periode_encodage: Optional[Tuple[datetime.date, datetime.date]],
    ) -> Optional[datetime.date]:
        deadlines: List[datetime.date] = []

        if date_defense_privee:
            deadlines.append(date_defense_privee - relativedelta(days=cls.ECHEANCE_NOMBRE_JOURS_AVANT_DEFENSE_PRIVEE))

        if periode_encodage:
            deadlines.append(periode_encodage[1])

        return min(deadlines, default=None)

    @classmethod
    def get_periode_encodage_notes(
        cls,
        annee: int,
        session: int,
    ) -> Optional[tuple[datetime.date]]:
        raise NotImplementedError
