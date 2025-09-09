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
from parcours_doctoral.ddd.defense_privee.domain.model.defense_privee import (
    DefensePrivee,
    DefensePriveeIdentity,
)
from parcours_doctoral.ddd.defense_privee.dtos import DefensePriveeDTO
from parcours_doctoral.ddd.defense_privee.validators.exceptions import (
    DefensePriveeNonTrouveeException,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)


class IDefensePriveeRepository(interface.AbstractRepository):
    @classmethod
    def search(cls, entity_ids: Optional[List['DefensePriveeIdentity']] = None, **kwargs) -> List[DefensePrivee]:
        raise NotImplementedError

    @classmethod
    def delete(cls, entity_id: 'DefensePriveeIdentity', **kwargs) -> None:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def save(cls, entity: 'DefensePrivee') -> 'DefensePriveeIdentity':
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def search_dto(
        cls,
        parcours_doctoral_id: Optional[ParcoursDoctoralIdentity] = None,
        entity_id: Optional['DefensePriveeIdentity'] = None,
        seulement_active: bool = False,
    ):
        raise NotImplementedError

    @classmethod
    def get_dto(cls, entity_id: 'DefensePriveeIdentity') -> 'DefensePriveeDTO':
        defenses_privees = cls.search_dto(entity_id=entity_id)

        if not defenses_privees:
            raise DefensePriveeNonTrouveeException

        return defenses_privees[0]

    @classmethod
    def get_active_dto_by_parcours_doctoral_identity(
        cls,
        parcours_doctoral_entity_id: 'ParcoursDoctoralIdentity',
    ) -> 'DefensePriveeDTO':
        defenses_privees = cls.search_dto(
            parcours_doctoral_id=parcours_doctoral_entity_id,
            seulement_active=True,
        )

        if not defenses_privees:
            raise DefensePriveeNonTrouveeException

        return defenses_privees[0]

    @classmethod
    def get(cls, entity_id: 'DefensePriveeIdentity') -> 'DefensePrivee':
        defense_privee = cls.get_dto(entity_id=entity_id)

        return DefensePrivee(
            entity_id=entity_id,
            parcours_doctoral_id=ParcoursDoctoralIdentity(uuid=defense_privee.uuid),
            est_active=defense_privee.est_active,
            date_heure=defense_privee.date_heure,
            lieu=defense_privee.lieu,
            date_envoi_manuscrit=defense_privee.date_envoi_manuscrit,
            proces_verbal=defense_privee.proces_verbal,
            canevas_proces_verbal=defense_privee.canevas_proces_verbal,
        )
