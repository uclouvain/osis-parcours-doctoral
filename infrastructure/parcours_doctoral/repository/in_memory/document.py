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
from typing import Dict, List

from osis_common.ddd.interface import EntityIdentity
from parcours_doctoral.ddd.domain.model.document import (
    Document,
    DocumentIdentity,
    TypeDocument,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.domain.validator.exceptions import DocumentNonTrouveException
from parcours_doctoral.ddd.dtos.document import DocumentDTO
from parcours_doctoral.ddd.repository.i_document import IDocumentRepository


class DocumentInMemoryRepository(IDocumentRepository):
    entities: List[Document] = None

    @classmethod
    def reset(cls):
        cls.entities = []

    def __init__(self):
        self.reset()

    @classmethod
    def get(cls, entity_id: DocumentIdentity) -> Document:
        try:
            return next(entity for entity in cls.entities if entity.entity_id == entity_id)
        except StopIteration:
            raise DocumentNonTrouveException

    @classmethod
    def get_dto(cls, entity_id: DocumentIdentity) -> DocumentDTO:
        entity = cls.get(entity_id)
        return cls._get_dto_from_entity(entity)

    @classmethod
    def get_dtos_parcours_doctoral(
        cls,
        parcours_doctoral_id: ParcoursDoctoralIdentity,
    ) -> Dict[str, List[DocumentDTO]]:
        documents = {
            TypeDocument.LIBRE.value: [],
            TypeDocument.SYSTEME.value: [],
        }

        for entity in cls.entities:
            if entity.entity_id.parcours_doctoral_id == parcours_doctoral_id:
                documents[entity.type.value].append(cls._get_dto_from_entity(entity))

        return documents

    @classmethod
    def save(cls, entity: Document) -> None:
        try:
            cls.delete(entity.entity_id)
        except DocumentNonTrouveException:
            pass

        cls.entities.append(entity)

    @classmethod
    def delete(cls, entity_id: EntityIdentity, **kwargs) -> None:
        index = next(((index for index, item in enumerate(cls.entities) if item.entity_id == entity_id)), None)

        if index is None:
            raise DocumentNonTrouveException

        del cls.entities[index]
