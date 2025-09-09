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
import datetime

from django.test import TestCase

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from parcours_doctoral.ddd.defense_privee.commands import SoumettreDefensePriveeCommand
from parcours_doctoral.ddd.defense_privee.test.factory.defense_privee import (
    DefensePriveeFactory,
)
from parcours_doctoral.ddd.defense_privee.validators.exceptions import (
    DefensePriveeNonCompleteeException,
)
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
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


class TestSoumettreDefensePrivee(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cmd = SoumettreDefensePriveeCommand
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
            'titre_these': 'Titre',
            'date_heure': datetime.datetime(2022, 1, 1),
            'lieu': 'Lieu',
            'date_envoi_manuscrit': datetime.date(2023, 1, 1),
        }

    def test_should_generer_exception_si_donnees_manquantes(self):
        self.parametres_cmd['date_heure'] = None

        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))
        self.assertIsInstance(e.exception.exceptions.pop(), DefensePriveeNonCompleteeException)

        self.parametres_cmd['date_heure'] = datetime.datetime(2022, 1, 1)
        self.parametres_cmd['titre_these'] = ''

        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))
        self.assertIsInstance(e.exception.exceptions.pop(), DefensePriveeNonCompleteeException)

    def test_should_soumettre_defense_privee_si_valide(self):
        parcours_doctoral_id_resultat = self.message_bus.invoke(self.cmd(**self.parametres_cmd))

        defense_privee_mise_a_jour = defense_privee.DefensePriveeInMemoryRepository.get(
            entity_id=self.defense_privee.entity_id,
        )

        parcours_doctoral = ParcoursDoctoralInMemoryRepository.get(defense_privee_mise_a_jour.parcours_doctoral_id)

        self.assertEqual(defense_privee_mise_a_jour.parcours_doctoral_id, parcours_doctoral_id_resultat)
        self.assertEqual(defense_privee_mise_a_jour.date_heure, self.parametres_cmd['date_heure'])
        self.assertEqual(defense_privee_mise_a_jour.lieu, self.parametres_cmd['lieu'])
        self.assertEqual(defense_privee_mise_a_jour.date_envoi_manuscrit, self.parametres_cmd['date_envoi_manuscrit'])

        self.assertEqual(parcours_doctoral.statut, ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE)
        self.assertEqual(parcours_doctoral.titre_these_propose, self.parametres_cmd['titre_these'])
