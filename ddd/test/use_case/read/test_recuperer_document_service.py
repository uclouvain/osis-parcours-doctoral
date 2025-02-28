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
import uuid

import freezegun
from django.test import TestCase

from parcours_doctoral.ddd.commands import (
    InitialiserDocumentCommand,
    RecupererDocumentQuery,
)
from parcours_doctoral.ddd.domain.model.document import DocumentIdentity, TypeDocument
from parcours_doctoral.ddd.domain.validator.exceptions import DocumentNonTrouveException
from parcours_doctoral.ddd.dtos.document import DocumentDTO
from parcours_doctoral.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from parcours_doctoral.infrastructure.parcours_doctoral.handlers_in_memory import (
    _document_repository,
)


class TestRecupererDocument(TestCase):
    @freezegun.freeze_time('2022-01-01')
    def setUp(self) -> None:
        self.document_repository = _document_repository
        self.addCleanup(self.document_repository.reset)
        self.cmd_initialisation = InitialiserDocumentCommand(
            uuid_parcours_doctoral=str(uuid.uuid4()),
            uuids_documents=['token-doc'],
            libelle='Libellé 1',
            type_document=TypeDocument.LIBRE.name,
            auteur='123456',
        )
        self.identite_document: DocumentIdentity = message_bus_in_memory_instance.invoke(self.cmd_initialisation)

    def test_recuperer_document_introuvable(self):
        cmd_recuperation = RecupererDocumentQuery(
            identifiant=str(uuid.uuid4()),
            uuid_parcours_doctoral=self.identite_document.parcours_doctoral_id.uuid,
        )

        with self.assertRaises(DocumentNonTrouveException):
            message_bus_in_memory_instance.invoke(cmd_recuperation)

    def test_recuperer_document(self):
        cmd_recuperation = RecupererDocumentQuery(
            identifiant=str(self.identite_document.identifiant),
            uuid_parcours_doctoral=self.identite_document.parcours_doctoral_id.uuid,
        )

        document_dto: DocumentDTO = message_bus_in_memory_instance.invoke(cmd_recuperation)

        self.assertEqual(document_dto.identifiant, self.identite_document.identifiant)
        self.assertEqual(document_dto.uuids_documents, self.cmd_initialisation.uuids_documents)
        self.assertEqual(document_dto.type, self.cmd_initialisation.type_document)
        self.assertEqual(document_dto.libelle, self.cmd_initialisation.libelle)
        self.assertEqual(document_dto.auteur, self.cmd_initialisation.auteur)
        self.assertEqual(document_dto.modifie_le, datetime.datetime(2022, 1, 1))
