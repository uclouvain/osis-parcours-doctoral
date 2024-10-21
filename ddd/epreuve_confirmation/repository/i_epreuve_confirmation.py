# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from parcours_doctoral.ddd.epreuve_confirmation.domain.model.epreuve_confirmation import (
    EpreuveConfirmation,
    EpreuveConfirmationIdentity,
)
from parcours_doctoral.ddd.epreuve_confirmation.dtos import EpreuveConfirmationDTO


class IEpreuveConfirmationRepository(interface.AbstractRepository):
    @classmethod
    @abc.abstractmethod
    def get(cls, entity_id: 'EpreuveConfirmationIdentity') -> 'EpreuveConfirmation':  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def search_by_parcours_doctoral_identity(
        cls, parcours_doctoral_entity_id: 'ParcoursDoctoralIdentity'
    ) -> List['EpreuveConfirmation']:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_dto(cls, entity_id: 'EpreuveConfirmationIdentity') -> 'EpreuveConfirmationDTO':
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def search_dto_by_parcours_doctoral_identity(
        cls, parcours_doctoral_entity_id: 'ParcoursDoctoralIdentity'
    ) -> List['EpreuveConfirmationDTO']:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_last_dto_by_parcours_doctoral_identity(
        cls, parcours_doctoral_entity_id: 'ParcoursDoctoralIdentity'
    ) -> 'EpreuveConfirmationDTO':
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def save(cls, entity: 'EpreuveConfirmation') -> 'EpreuveConfirmationIdentity':  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    def search(  # type: ignore[override]
        cls,
        entity_ids: Optional[List['EpreuveConfirmationIdentity']] = None,
        **kwargs,
    ) -> List[EpreuveConfirmation]:
        raise NotImplementedError

    @classmethod
    def delete(cls, entity_id: 'EpreuveConfirmationIdentity', **kwargs) -> None:  # type: ignore[override]
        raise NotImplementedError
