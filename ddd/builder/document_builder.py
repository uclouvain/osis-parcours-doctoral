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

import datetime

from osis_common.ddd import interface
from osis_common.ddd.interface import CommandRequest
from parcours_doctoral.ddd.builder.document_identity_builder import (
    DocumentIdentityBuilder,
)
from parcours_doctoral.ddd.domain.model.document import Document, TypeDocument
from parcours_doctoral.ddd.dtos.document import DocumentDTO


class DocumentBuilder(interface.RootEntityBuilder):
    @classmethod
    def build_from_command(cls, cmd: 'CommandRequest') -> 'Document':
        raise NotImplementedError

    @classmethod
    def build_from_repository_dto(cls, dto_object: 'DocumentDTO') -> 'Document':
        raise NotImplementedError

    @classmethod
    def initialiser_document(
        cls,
        uuid_parcours_doctoral: str,
        auteur: str,
        libelle: str,
        type_document: str,
    ) -> 'Document':
        return Document(
            entity_id=DocumentIdentityBuilder.build(
                uuid_parcours_doctoral=uuid_parcours_doctoral,
            ),
            type=TypeDocument[type_document],
            libelle=libelle,
            modifie_le=datetime.datetime.now(),
            auteur=auteur,
            uuids_documents=[],
        )
