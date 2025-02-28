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
from typing import List

import freezegun
from django.test import TestCase

from parcours_doctoral.ddd.commands import (
    InitialiserDocumentCommand,
    ListerDocumentsQuery,
)
from parcours_doctoral.ddd.domain.model.document import DocumentIdentity, TypeDocument
from parcours_doctoral.ddd.dtos.document import DocumentDTO
from parcours_doctoral.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from parcours_doctoral.infrastructure.parcours_doctoral.handlers_in_memory import (
    _document_repository,
)


class TestListerDocuments(TestCase):
    @freezegun.freeze_time('2022-01-01')
    def setUp(self) -> None:
        self.document_repository = _document_repository
        self.addCleanup(self.document_repository.reset)
        self.cmd_initialisation_1 = InitialiserDocumentCommand(
            uuid_parcours_doctoral=str(uuid.uuid4()),
            uuids_documents=['token-doc-1'],
            libelle='Libellé 1',
            type_document=TypeDocument.LIBRE.name,
            auteur='123456',
        )
        self.identite_document_1: DocumentIdentity = message_bus_in_memory_instance.invoke(self.cmd_initialisation_1)
        self.cmd_initialisation_2 = InitialiserDocumentCommand(
            uuid_parcours_doctoral=self.cmd_initialisation_1.uuid_parcours_doctoral,
            uuids_documents=['token-doc-2'],
            libelle='Libellé 2',
            type_document=TypeDocument.SYSTEME.name,
            auteur='987654',
        )
        self.identite_document_2: DocumentIdentity = message_bus_in_memory_instance.invoke(self.cmd_initialisation_2)

    def test_lister_documents(self):
        cmd_listing = ListerDocumentsQuery(uuid_parcours_doctoral=self.cmd_initialisation_1.uuid_parcours_doctoral)

        dtos: List[DocumentDTO] = message_bus_in_memory_instance.invoke(cmd_listing)

        self.assertEqual(dtos[TypeDocument.LIBRE.value][0].identifiant, self.identite_document_1.identifiant)
        self.assertEqual(dtos[TypeDocument.LIBRE.value][0].uuids_documents, self.cmd_initialisation_1.uuids_documents)
        self.assertEqual(dtos[TypeDocument.LIBRE.value][0].type, self.cmd_initialisation_1.type_document)
        self.assertEqual(dtos[TypeDocument.LIBRE.value][0].libelle, self.cmd_initialisation_1.libelle)
        self.assertEqual(dtos[TypeDocument.LIBRE.value][0].auteur, self.cmd_initialisation_1.auteur)
        self.assertEqual(dtos[TypeDocument.LIBRE.value][0].modifie_le, datetime.datetime(2022, 1, 1))

        self.assertEqual(dtos[TypeDocument.SYSTEME.value][0].identifiant, self.identite_document_2.identifiant)
        self.assertEqual(dtos[TypeDocument.SYSTEME.value][0].uuids_documents, self.cmd_initialisation_2.uuids_documents)
        self.assertEqual(dtos[TypeDocument.SYSTEME.value][0].type, self.cmd_initialisation_2.type_document)
        self.assertEqual(dtos[TypeDocument.SYSTEME.value][0].libelle, self.cmd_initialisation_2.libelle)
        self.assertEqual(dtos[TypeDocument.SYSTEME.value][0].auteur, self.cmd_initialisation_2.auteur)
        self.assertEqual(dtos[TypeDocument.SYSTEME.value][0].modifie_le, datetime.datetime(2022, 1, 1))
