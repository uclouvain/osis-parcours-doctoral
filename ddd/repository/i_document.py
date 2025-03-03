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
from abc import ABCMeta, abstractmethod
from typing import Dict, List, Optional

from osis_common.ddd import interface
from osis_common.ddd.interface import EntityIdentity, RootEntity
from parcours_doctoral.ddd.domain.model.document import Document, DocumentIdentity
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.dtos.document import DocumentDTO


class IDocumentRepository(interface.AbstractRepository, metaclass=ABCMeta):
    @classmethod
    def _get_dto_from_entity(cls, entity: Document) -> DocumentDTO:
        return DocumentDTO(
            identifiant=entity.entity_id.identifiant,
            uuids_documents=entity.uuids_documents,
            type=entity.type.name,
            libelle=entity.libelle,
            auteur=entity.auteur,
            modifie_le=entity.modifie_le,
        )

    @classmethod
    @abstractmethod
    def get(cls, entity_id: DocumentIdentity) -> Document:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_dto(cls, entity_id: DocumentIdentity) -> DocumentDTO:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_dtos_parcours_doctoral(
        cls,
        parcours_doctoral_id: ParcoursDoctoralIdentity,
    ) -> Dict[str, List[DocumentDTO]]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def save(cls, entity: Document) -> None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def delete(cls, entity_id: EntityIdentity, **kwargs) -> None:
        raise NotImplementedError

    @classmethod
    def search(cls, entity_ids: Optional[List[EntityIdentity]] = None, **kwargs) -> List[RootEntity]:
        raise NotImplementedError
