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

from parcours_doctoral.ddd.builder.document_builder import DocumentBuilder
from parcours_doctoral.ddd.commands import InitialiserDocumentCommand
from parcours_doctoral.ddd.domain.model.document import DocumentIdentity
from parcours_doctoral.ddd.repository.i_document import IDocumentRepository


def initialiser_document(
    cmd: 'InitialiserDocumentCommand',
    document_repository: 'IDocumentRepository',
) -> DocumentIdentity:
    document = DocumentBuilder().initialiser_document(
        uuid_parcours_doctoral=cmd.uuid_parcours_doctoral,
        auteur=cmd.auteur,
        libelle=cmd.libelle,
        type_document=cmd.type_document,
    )

    document.modifier(uuids_documents=cmd.uuids_documents, auteur=cmd.auteur)

    document_repository.save(document)

    return document.entity_id
