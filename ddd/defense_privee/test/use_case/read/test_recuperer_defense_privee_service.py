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

from django.test import TestCase

from parcours_doctoral.ddd.defense_privee.commands import RecupererDefensePriveeQuery
from parcours_doctoral.ddd.defense_privee.dtos import DefensePriveeDTO
from parcours_doctoral.ddd.defense_privee.test.factory.defense_privee import (
    DefensePriveeFactory,
)
from parcours_doctoral.ddd.defense_privee.validators.exceptions import (
    DefensePriveeNonTrouveeException,
)
from parcours_doctoral.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from parcours_doctoral.infrastructure.parcours_doctoral.defense_privee.repository.in_memory.defense_privee import (
    DefensePriveeInMemoryRepository,
)


class TestRecupererDefensePrivee(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cmd = RecupererDefensePriveeQuery
        cls.message_bus = message_bus_in_memory_instance
        cls.defense_privee_repository = DefensePriveeInMemoryRepository()

    def setUp(self):
        self.addCleanup(DefensePriveeInMemoryRepository.reset)
        self.defense_privee = DefensePriveeFactory()
        self.defense_privee_repository.save(self.defense_privee)

    def test_should_pas_trouver_si_defense_inconnue(self):
        with self.assertRaises(DefensePriveeNonTrouveeException):
            self.message_bus.invoke(self.cmd(uuid='inconnu'))

    def test_should_retourner_defense_privee(self):
        defense_privee: DefensePriveeDTO = self.message_bus.invoke(self.cmd(uuid=self.defense_privee.entity_id.uuid))
        self.assertEqual(defense_privee.uuid, self.defense_privee.entity_id.uuid)
