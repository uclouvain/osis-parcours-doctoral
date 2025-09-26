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
from django.test import SimpleTestCase

from parcours_doctoral.ddd.jury.commands import ApprouverJuryParCddCommand
from parcours_doctoral.ddd.jury.domain.model.enums import ChoixEtatSignature, RoleJury
from parcours_doctoral.ddd.jury.domain.model.jury import JuryIdentity
from parcours_doctoral.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from parcours_doctoral.infrastructure.parcours_doctoral.jury.repository.in_memory.jury import (
    JuryInMemoryRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.repository.in_memory.parcours_doctoral import (
    ParcoursDoctoralInMemoryRepository,
)


class TestApprouverJuryParCdd(SimpleTestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance

    def tearDown(self) -> None:
        JuryInMemoryRepository.reset()
        ParcoursDoctoralInMemoryRepository.reset()

    def test_approuver_jury(self):
        self.message_bus.invoke(
            ApprouverJuryParCddCommand(
                uuid_jury='uuid-SC3DP-promoteur-deja-approuve',
                matricule_auteur='012346789',
                commentaire_interne='Commentaire interne',
                commentaire_externe='Commentaire externe',
            )
        )

        jury = JuryInMemoryRepository.get(JuryIdentity(uuid='uuid-SC3DP-promoteur-deja-approuve'))
        membre = next(m for m in jury.membres if m.role == RoleJury.CDD)
        self.assertEqual(membre.signature.etat, ChoixEtatSignature.APPROVED)
        self.assertEqual(membre.signature.commentaire_interne, 'Commentaire interne')
        self.assertEqual(membre.signature.commentaire_externe, 'Commentaire externe')
