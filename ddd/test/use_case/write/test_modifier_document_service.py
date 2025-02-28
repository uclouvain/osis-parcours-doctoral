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
    ModifierDocumentCommand,
)
from parcours_doctoral.ddd.domain.model.document import DocumentIdentity, TypeDocument
from parcours_doctoral.ddd.domain.validator.exceptions import DocumentNonTrouveException
from parcours_doctoral.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from parcours_doctoral.infrastructure.parcours_doctoral.handlers_in_memory import (
    _document_repository,
)


class TestModifierDocument(TestCase):
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

    @freezegun.freeze_time('2023-02-02')
    def test_modifier_document(self):
        cmd_remplissage = ModifierDocumentCommand(
            identifiant=str(self.identite_document.identifiant),
            uuid_parcours_doctoral=self.identite_document.parcours_doctoral_id.uuid,
            uuids_documents=['nouveau-token-doc'],
            auteur='654321',
        )

        with freezegun.freeze_time('2023-02-02'):
            identite_document_mis_a_jour = message_bus_in_memory_instance.invoke(cmd_remplissage)

        self.assertEqual(self.identite_document, identite_document_mis_a_jour)

        document = self.document_repository.get(entity_id=self.identite_document)

        self.assertEqual(document.entity_id, identite_document_mis_a_jour)
        self.assertEqual(document.uuids_documents, cmd_remplissage.uuids_documents)
        self.assertEqual(document.type, TypeDocument[self.cmd_initialisation.type_document])
        self.assertEqual(document.modifie_le, datetime.datetime(2023, 2, 2))
        self.assertEqual(document.auteur, cmd_remplissage.auteur)
        self.assertEqual(document.libelle, self.cmd_initialisation.libelle)

    def test_modifier_document_introuvable(self):
        cmd_remplissage = ModifierDocumentCommand(
            identifiant=str(uuid.uuid4()),
            uuid_parcours_doctoral=self.identite_document.parcours_doctoral_id.uuid,
            uuids_documents=['nouveau-token-doc'],
            auteur='654321',
        )

        with self.assertRaises(DocumentNonTrouveException):
            message_bus_in_memory_instance.invoke(cmd_remplissage)
