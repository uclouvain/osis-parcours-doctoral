# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
import abc
from typing import List, Optional, Union

from osis_common.ddd import interface
from osis_common.ddd.interface import ApplicationService

from parcours_doctoral.ddd.domain.model.groupe_de_supervision import (
    GroupeDeSupervision,
    GroupeDeSupervisionIdentity,
    SignataireIdentity,
)
from parcours_doctoral.ddd.dtos import MembreCADTO, PromoteurDTO
from parcours_doctoral.models import ActorType


class IGroupeDeSupervisionRepository(interface.AbstractRepository):
    @classmethod
    @abc.abstractmethod
    def get(cls, entity_id: 'GroupeDeSupervisionIdentity') -> 'GroupeDeSupervision':  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_by_parcours_doctoral_id(cls, parcours_doctoral_id: 'ParcoursDoctoralIdentity') -> 'GroupeDeSupervision':
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def search(  # type: ignore[override]
        cls,
        entity_ids: Optional[List['GroupeDeSupervisionIdentity']] = None,
        matricule_membre: str = None,
        **kwargs,
    ) -> List['GroupeDeSupervision']:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def delete(  # type: ignore[override]
        cls,
        entity_id: 'GroupeDeSupervisionIdentity',
        **kwargs: ApplicationService,
    ) -> None:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def save(cls, entity: 'GroupeDeSupervision') -> None:  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def add_member(
        cls,
        groupe_id: 'GroupeDeSupervisionIdentity',
        type: ActorType,
        matricule: Optional[str] = '',
        first_name: Optional[str] = '',
        last_name: Optional[str] = '',
        email: Optional[str] = '',
        is_doctor: Optional[bool] = False,
        institute: Optional[str] = '',
        city: Optional[str] = '',
        country_code: Optional[str] = '',
        language: Optional[str] = '',
    ) -> 'SignataireIdentity':
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def edit_external_member(
        cls,
        groupe_id: 'GroupeDeSupervisionIdentity',
        membre_id: 'SignataireIdentity',
        first_name: Optional[str] = '',
        last_name: Optional[str] = '',
        email: Optional[str] = '',
        is_doctor: Optional[bool] = False,
        institute: Optional[str] = '',
        city: Optional[str] = '',
        country_code: Optional[str] = '',
        language: Optional[str] = '',
    ) -> None:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def remove_member(cls, groupe_id: 'GroupeDeSupervisionIdentity', signataire: 'SignataireIdentity') -> None:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_members(cls, groupe_id: 'GroupeDeSupervisionIdentity') -> List[Union['PromoteurDTO', 'MembreCADTO']]:
        raise NotImplementedError
