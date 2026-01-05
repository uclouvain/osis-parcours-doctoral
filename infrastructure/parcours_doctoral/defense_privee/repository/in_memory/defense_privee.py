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
    DefensePriveeIdentity,
)
from parcours_doctoral.ddd.defense_privee.dtos import DefensePriveeDTO
from parcours_doctoral.ddd.defense_privee.repository.i_defense_privee import (
    IDefensePriveeRepository,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)


class DefensePriveeInMemoryRepository(InMemoryGenericRepository, IDefensePriveeRepository):
    @classmethod
    def search_dto(
        cls,
        parcours_doctoral_id: Optional[ParcoursDoctoralIdentity] = None,
        entity_id: Optional['DefensePriveeIdentity'] = None,
        seulement_active: bool = False,
    ) -> List['DefensePriveeDTO']:
        entities = [
            DefensePriveeDTO(
                uuid=entity.entity_id.uuid,
                est_active=entity.est_active,
                date_heure=entity.date_heure,
                lieu=entity.lieu,
                date_envoi_manuscrit=entity.date_envoi_manuscrit,
                proces_verbal=entity.proces_verbal,
                canevas_proces_verbal=entity.canevas_proces_verbal,
                parcours_doctoral_uuid=entity.parcours_doctoral_id.uuid,
            )
            for entity in cls.entities
            if (not parcours_doctoral_id or entity.parcours_doctoral_id == parcours_doctoral_id)
            and (not seulement_active or entity.est_active)
            and (not entity_id or entity.entity_id == entity_id)
        ]

        return entities
