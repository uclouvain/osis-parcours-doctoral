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
from parcours_doctoral.ddd.recevabilite.builder.recevabilite import RecevabiliteBuilder
from parcours_doctoral.ddd.recevabilite.domain.model.recevabilite import (
    Recevabilite,
    RecevabiliteIdentity,
)
from parcours_doctoral.ddd.recevabilite.dtos import RecevabiliteDTO
from parcours_doctoral.ddd.recevabilite.validators.exceptions import (
    RecevabiliteNonTrouveeException,
)


class IRecevabiliteRepository(interface.AbstractRepository):
    @classmethod
    def search(cls, entity_ids: Optional[List['RecevabiliteIdentity']] = None, **kwargs) -> List[Recevabilite]:
        raise NotImplementedError

    @classmethod
    def delete(cls, entity_id: 'RecevabiliteIdentity', **kwargs) -> None:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def save(cls, entity: 'Recevabilite') -> 'RecevabiliteIdentity':
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def search_dto(
        cls,
        parcours_doctoral_id: Optional[ParcoursDoctoralIdentity] = None,
        entity_id: Optional['RecevabiliteIdentity'] = None,
        seulement_active: bool = False,
    ):
        raise NotImplementedError

    @classmethod
    def get_dto(cls, entity_id: 'RecevabiliteIdentity') -> 'RecevabiliteDTO':
        defenses_privees = cls.search_dto(entity_id=entity_id)

        if not defenses_privees:
            raise RecevabiliteNonTrouveeException

        return defenses_privees[0]

    @classmethod
    def get_active_dto_by_parcours_doctoral_identity(
        cls,
        parcours_doctoral_entity_id: 'ParcoursDoctoralIdentity',
    ) -> 'RecevabiliteDTO':
        defenses_privees = cls.search_dto(
            parcours_doctoral_id=parcours_doctoral_entity_id,
            seulement_active=True,
        )

        if not defenses_privees:
            raise RecevabiliteNonTrouveeException

        return defenses_privees[0]

    @classmethod
    def get(cls, entity_id: 'RecevabiliteIdentity') -> 'Recevabilite':
        recevabilite = cls.get_dto(entity_id=entity_id)
        return RecevabiliteBuilder.build_from_repository_dto(recevabilite)

    @classmethod
    def get_active(cls, parcours_doctoral_entity_id: 'ParcoursDoctoralIdentity') -> 'Recevabilite':
        try:
            recevabilite = cls.get_active_dto_by_parcours_doctoral_identity(parcours_doctoral_entity_id)
            return RecevabiliteBuilder.build_from_repository_dto(recevabilite)
        except RecevabiliteNonTrouveeException:
            return RecevabiliteBuilder.build_from_parcours_doctoral_id(parcours_doctoral_id=parcours_doctoral_entity_id)
