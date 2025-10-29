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
from typing import List

from django.test import TestCase

from parcours_doctoral.ddd.defense_privee.commands import RecupererDefensesPriveesQuery
from parcours_doctoral.ddd.defense_privee.dtos import DefensePriveeDTO
from parcours_doctoral.ddd.defense_privee.test.factory.defense_privee import (
    DefensePriveeFactory,
)
from parcours_doctoral.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from parcours_doctoral.infrastructure.parcours_doctoral.defense_privee.repository.in_memory.defense_privee import (
    DefensePriveeInMemoryRepository,
)


class TestRecupererDefensesPrivees(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cmd = RecupererDefensesPriveesQuery
        cls.message_bus = message_bus_in_memory_instance
        cls.defense_privee_repository = DefensePriveeInMemoryRepository()

    def setUp(self):
        self.addCleanup(DefensePriveeInMemoryRepository.reset)
        self.defense_privee_1 = DefensePriveeFactory()
        self.defense_privee_2 = DefensePriveeFactory(
            est_active=False,
            parcours_doctoral_id=self.defense_privee_1.parcours_doctoral_id,
        )
        self.defense_privee_repository.save(self.defense_privee_1)
        self.defense_privee_repository.save(self.defense_privee_2)

    def test_should_retourner_defenses(self):
        defenses_privees: List[DefensePriveeDTO] = self.message_bus.invoke(
            self.cmd(parcours_doctoral_uuid=self.defense_privee_1.parcours_doctoral_id.uuid)
        )
        self.assertEqual(len(defenses_privees), 2)
        self.assertCountEqual(
            [defenses_privees[0].uuid, defenses_privees[1].uuid],
            [self.defense_privee_1.entity_id.uuid, self.defense_privee_2.entity_id.uuid],
        )
