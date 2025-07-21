# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from typing import List, Optional

from base.ddd.utils.in_memory_repository import InMemoryGenericRepository
from parcours_doctoral.ddd.defense_privee.domain.model.defense_privee import (
    DefensePrivee,
    DefensePriveeIdentity,
)
from parcours_doctoral.ddd.defense_privee.dtos import DefensePriveeDTO
from parcours_doctoral.ddd.defense_privee.repository.i_defense_privee import (
    IDefensePriveeRepository,
)
from parcours_doctoral.ddd.defense_privee.validators.exceptions import (
    DefensePriveeNonTrouveeException,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)


class DefensePriveeInMemoryRepository(InMemoryGenericRepository, IDefensePriveeRepository):
    @classmethod
    def get(cls, entity_id: 'DefensePriveeIdentity') -> 'DefensePrivee':
        entity = super().get(entity_id)

        if not entity:
            raise DefensePriveeNonTrouveeException

        return entity

    @classmethod
    def build_dto_from_model(cls, entity: 'DefensePrivee') -> 'DefensePriveeDTO':
        return DefensePriveeDTO(
            uuid=entity.entity_id.uuid,
            est_active=entity.est_active,
            titre_these='',
            date_heure=entity.date_heure,
            lieu=entity.lieu,
            date_envoi_manuscrit=entity.date_envoi_manuscrit,
            proces_verbal=entity.proces_verbal,
            canevas_proces_verbal=entity.canevas_proces_verbal,
        )

    @classmethod
    def get_dto(cls, entity_id: 'DefensePriveeIdentity') -> 'DefensePriveeDTO':
        entity = cls.get(entity_id=entity_id)
        return cls.build_dto_from_model(entity=entity)

    @classmethod
    def search_dto_by_parcours_doctoral_identity(
        cls,
        parcours_doctoral_entity_id: 'ParcoursDoctoralIdentity',
    ) -> List['DefensePriveeDTO']:
        return [
            cls.build_dto_from_model(entity=entity)
            for entity in cls.entities
            if entity.parcours_doctoral_id == parcours_doctoral_entity_id
        ]

    @classmethod
    def get_active_dto_by_parcours_doctoral_identity(
        cls,
        parcours_doctoral_entity_id: 'ParcoursDoctoralIdentity',
    ) -> 'DefensePriveeDTO':
        entity: Optional[DefensePrivee] = next(
            (
                entity
                for entity in cls.entities
                if entity.est_active and entity.parcours_doctoral_id == parcours_doctoral_entity_id
            ),
            None,
        )

        if not entity:
            raise DefensePriveeNonTrouveeException

        return cls.build_dto_from_model(entity)
