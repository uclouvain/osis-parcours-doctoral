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
from typing import List, Optional

from osis_common.ddd import interface
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.formation.domain.model.activite import ActiviteIdentity
from parcours_doctoral.ddd.formation.domain.model.inscription_evaluation import (
    InscriptionEvaluation,
    InscriptionEvaluationIdentity,
)
from parcours_doctoral.ddd.formation.dtos.evaluation import InscriptionEvaluationDTO


class IInscriptionEvaluationRepository(interface.AbstractRepository):
    @classmethod
    @abc.abstractmethod
    def get(cls, entity_id: 'InscriptionEvaluationIdentity') -> 'InscriptionEvaluation':  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_dto(cls, entity_id: 'InscriptionEvaluationIdentity') -> 'InscriptionEvaluationDTO':
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def delete(cls, entity_id: 'InscriptionEvaluationIdentity', **kwargs) -> None:  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def save(cls, entity: 'InscriptionEvaluation') -> None:  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def search(
        cls,
        cours_id: Optional[ActiviteIdentity] = None,
        parcours_doctoral_id: Optional[ParcoursDoctoralIdentity] = None,
        **kwargs,
    ) -> List[InscriptionEvaluation]:  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def search_dto(
        cls,
        cours_uuid: Optional[str] = None,
        parcours_doctoral_id: Optional[str] = None,
        **kwargs,
    ) -> List[InscriptionEvaluationDTO]:  # type: ignore[override]
        raise NotImplementedError
