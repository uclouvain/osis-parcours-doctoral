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
from osis_common.ddd.interface import ApplicationService, EntityIdentity, RootEntity
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.autorisation_diffusion_these import (
    AutorisationDiffusionThese,
    AutorisationDiffusionTheseIdentity,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.dtos.autorisation_diffusion_these import (
    AutorisationDiffusionTheseDTO,
)


class IAutorisationDiffusionTheseRepository(interface.AbstractRepository):
    @classmethod
    def delete(cls, entity_id: EntityIdentity, **kwargs: ApplicationService) -> None:
        raise NotImplementedError

    @classmethod
    def search(cls, entity_ids: Optional[List[EntityIdentity]] = None, **kwargs) -> List[RootEntity]:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get(
        cls,
        entity_id: 'AutorisationDiffusionTheseIdentity',
    ) -> 'AutorisationDiffusionThese':  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_dto(cls, entity_id: 'AutorisationDiffusionTheseIdentity') -> 'AutorisationDiffusionTheseDTO':
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def save(
        cls,
        entity: 'AutorisationDiffusionThese',
    ) -> 'AutorisationDiffusionTheseIdentity':  # type: ignore[override]
        raise NotImplementedError
