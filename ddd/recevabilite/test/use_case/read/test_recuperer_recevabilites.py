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

from parcours_doctoral.ddd.recevabilite.commands import RecupererRecevabilitesQuery
from parcours_doctoral.ddd.recevabilite.dtos import RecevabiliteDTO
from parcours_doctoral.ddd.recevabilite.test.factory.recevabilite import (
    RecevabiliteFactory,
)
from parcours_doctoral.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from parcours_doctoral.infrastructure.parcours_doctoral.recevabilite.repository.in_memory.recevabilite import (
    RecevabiliteInMemoryRepository,
)


class TestRecupererRecevabilites(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cmd = RecupererRecevabilitesQuery
        cls.message_bus = message_bus_in_memory_instance
        cls.recevabilite_repository = RecevabiliteInMemoryRepository()

    def setUp(self):
        self.addCleanup(RecevabiliteInMemoryRepository.reset)
        self.recevabilite_1 = RecevabiliteFactory()
        self.recevabilite_2 = RecevabiliteFactory(
            est_active=False,
            parcours_doctoral_id=self.recevabilite_1.parcours_doctoral_id,
        )
        self.recevabilite_repository.save(self.recevabilite_1)
        self.recevabilite_repository.save(self.recevabilite_2)

    def test_should_retourner_recevabilites(self):
        recevabilites: List[RecevabiliteDTO] = self.message_bus.invoke(
            self.cmd(parcours_doctoral_uuid=self.recevabilite_1.parcours_doctoral_id.uuid)
        )
        self.assertEqual(len(recevabilites), 2)
        self.assertCountEqual(
            [recevabilites[0].uuid, recevabilites[1].uuid],
            [self.recevabilite_1.entity_id.uuid, self.recevabilite_2.entity_id.uuid],
        )
