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

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from parcours_doctoral.ddd.defense_privee.commands import (
    SoumettreProcesVerbalDefensePriveeCommand,
)
from parcours_doctoral.ddd.defense_privee.test.factory.defense_privee import (
    DefensePriveeFactory,
)
from parcours_doctoral.ddd.defense_privee.validators.exceptions import (
    DefensePriveeNonActiveeException,
)
from parcours_doctoral.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from parcours_doctoral.infrastructure.parcours_doctoral.defense_privee.repository.in_memory import (
    defense_privee,
)
from parcours_doctoral.infrastructure.parcours_doctoral.defense_privee.repository.in_memory.defense_privee import (
    DefensePriveeInMemoryRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.repository.in_memory.parcours_doctoral import (
    ParcoursDoctoralInMemoryRepository,
)


class TestSoumettreProcesVerbalDefensePrivee(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cmd = SoumettreProcesVerbalDefensePriveeCommand
        cls.message_bus = message_bus_in_memory_instance
        cls.defense_privee_repository = DefensePriveeInMemoryRepository()
        cls.parcours_doctoral_repository = ParcoursDoctoralInMemoryRepository()

    def setUp(self):
        self.addCleanup(DefensePriveeInMemoryRepository.reset)
        self.addCleanup(ParcoursDoctoralInMemoryRepository.reset)
        self.defense_privee = DefensePriveeFactory(
            parcours_doctoral_id=self.parcours_doctoral_repository.entities[0].entity_id,
        )
        self.defense_privee_repository.save(self.defense_privee)
        self.parametres_cmd = {
            'uuid': self.defense_privee.entity_id.uuid,
            'matricule_auteur': '1234',
            'proces_verbal': ['file-uuid'],
        }

    def test_should_lever_exception_si_defense_privee_inactive(self):
        defense_privee = self.defense_privee_repository.get(entity_id=self.defense_privee.entity_id)
        defense_privee.est_active = False

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))

        self.assertIsInstance(context.exception.exceptions.pop(), DefensePriveeNonActiveeException)

    def test_should_soumettre_proces_verbal_defense_privee(self):
        parcours_doctoral_id_resultat = self.message_bus.invoke(self.cmd(**self.parametres_cmd))

        defense_privee_mise_a_jour = defense_privee.DefensePriveeInMemoryRepository.get(
            entity_id=self.defense_privee.entity_id,
        )

        self.assertEqual(defense_privee_mise_a_jour.parcours_doctoral_id, parcours_doctoral_id_resultat)
        self.assertEqual(defense_privee_mise_a_jour.proces_verbal, self.parametres_cmd['proces_verbal'])
