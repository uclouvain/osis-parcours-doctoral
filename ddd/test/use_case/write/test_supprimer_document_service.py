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
import uuid

from django.test import TestCase

from parcours_doctoral.ddd.commands import (
    InitialiserDocumentCommand,
    SupprimerDocumentCommand,
)
from parcours_doctoral.ddd.domain.model.document import DocumentIdentity, TypeDocument
from parcours_doctoral.ddd.domain.validator.exceptions import DocumentNonTrouveException
from parcours_doctoral.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from parcours_doctoral.infrastructure.parcours_doctoral.handlers_in_memory import (
    _document_repository,
)


class TestSupprimerDocument(TestCase):
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

    def test_supprimer_document(self):
        cmd_suppression = SupprimerDocumentCommand(
            identifiant=str(self.identite_document.identifiant),
            uuid_parcours_doctoral=self.identite_document.parcours_doctoral_id.uuid,
        )

        identite_document_supprime = message_bus_in_memory_instance.invoke(cmd_suppression)

        self.assertEqual(self.identite_document, identite_document_supprime)

        with self.assertRaises(DocumentNonTrouveException):
            self.document_repository.get(entity_id=self.identite_document)

    def test_supprimer_document_introuvable(self):
        cmd_suppression = SupprimerDocumentCommand(
            identifiant=str(uuid.uuid4()),
            uuid_parcours_doctoral=self.identite_document.parcours_doctoral_id.uuid,
        )

        with self.assertRaises(DocumentNonTrouveException):
            message_bus_in_memory_instance.invoke(cmd_suppression)
