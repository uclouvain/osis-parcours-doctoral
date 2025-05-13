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
from typing import List, Optional

from base.ddd.utils.in_memory_repository import InMemoryGenericRepository
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.formation.domain.model.activite import ActiviteIdentity
from parcours_doctoral.ddd.formation.domain.model.inscription_evaluation import (
    InscriptionEvaluation,
    InscriptionEvaluationIdentity,
)
from parcours_doctoral.ddd.formation.dtos.inscription_evaluation import (
    InscriptionEvaluationDTO,
)
from parcours_doctoral.ddd.formation.repository.i_inscription_evaluation import (
    IInscriptionEvaluationRepository,
)


class InscriptionEvaluationInMemoryRepository(InMemoryGenericRepository, IInscriptionEvaluationRepository):
    entities: List['InscriptionEvaluation']

    @classmethod
    def _get_dto_from_domain_object(
        cls,
        enrollment: InscriptionEvaluation,
    ) -> InscriptionEvaluationDTO:
        annee = 2020
        return InscriptionEvaluationDTO(
            uuid=str(enrollment.entity_id.uuid),
            uuid_activite=str(enrollment.cours_id.uuid),
            session=enrollment.session.name,
            inscription_tardive=enrollment.inscription_tardive,
            code_unite_enseignement='',
            intitule_unite_enseignement='',
            annee_unite_enseignement=annee,
            statut=enrollment.statut.name,
            desinscription_tardive=enrollment.desinscription_tardive,
        )

    @classmethod
    def get_dto(
        cls,
        entity_id: 'InscriptionEvaluationIdentity',
    ) -> 'InscriptionEvaluationDTO':
        return cls._get_dto_from_domain_object(cls.get(entity_id))

    @classmethod
    def search(
        cls,
        cours_id: Optional[ActiviteIdentity] = None,
        parcours_doctoral_id: Optional[ParcoursDoctoralIdentity] = None,
        **kwargs,
    ) -> List[InscriptionEvaluation]:  # type: ignore[override]
        if cours_id:
            return [entity for entity in cls.entities if entity.cours_id == cours_id]
        return cls.entities

    @classmethod
    def search_dto(
        cls,
        cours_uuid: Optional[str] = None,
        parcours_doctoral_id: Optional[str] = None,
        annee: Optional[int] = None,
        session: Optional[int] = None,
        code_unite_enseignement: Optional[str] = None,
        noma: Optional[str] = None,
        **kwargs,
    ) -> List[InscriptionEvaluationDTO]:  # type: ignore[override]
        return [
            cls._get_dto_from_domain_object(entity) for entity in cls.search(cours_uuid, parcours_doctoral_id, **kwargs)
        ]
