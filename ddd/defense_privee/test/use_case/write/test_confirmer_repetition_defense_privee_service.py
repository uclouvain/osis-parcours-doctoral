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
    ConfirmerRepetitionDefensePriveeCommand,
    ConfirmerReussiteDefensePriveeCommand,
)
from parcours_doctoral.ddd.defense_privee.test.factory.defense_privee import (
    DefensePriveeFactory,
)
from parcours_doctoral.ddd.defense_privee.validators.exceptions import (
    DefensePriveeNonCompleteePourDecisionException,
    DefensePriveeNonTrouveeException,
    StatutDoctoratDifferentDefensePriveeAutoriseeException,
)
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.domain.validator.exceptions import (
    ParcoursDoctoralNonTrouveException,
)
from parcours_doctoral.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from parcours_doctoral.infrastructure.parcours_doctoral.defense_privee.repository.in_memory.defense_privee import (
    DefensePriveeInMemoryRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.repository.in_memory.parcours_doctoral import (
    ParcoursDoctoralInMemoryRepository,
)


class TestConfirmerRepetitionDefensePrivee(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cmd = ConfirmerRepetitionDefensePriveeCommand
        cls.message_bus = message_bus_in_memory_instance
        cls.defense_privee_repository = DefensePriveeInMemoryRepository()
        cls.parcours_doctoral_repository = ParcoursDoctoralInMemoryRepository()

    def setUp(self):
        self.addCleanup(DefensePriveeInMemoryRepository.reset)
        self.addCleanup(ParcoursDoctoralInMemoryRepository.reset)
        self.parcours_doctoral = self.parcours_doctoral_repository.entities[0]
        self.parcours_doctoral.statut = ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_AUTORISEE
        self.defense_privee = DefensePriveeFactory(parcours_doctoral_id=self.parcours_doctoral.entity_id)
        self.defense_privee_repository.save(self.defense_privee)
        self.parametres_cmd = {
            'parcours_doctoral_uuid': self.parcours_doctoral.entity_id.uuid,
            'matricule_auteur': '1234',
            'corps_message': 'Corps',
            'sujet_message': 'Sujet',
        }

    def test_should_generer_exception_si_parcours_doctoral_inconnu(self):
        self.parametres_cmd['parcours_doctoral_uuid'] = 'INCONNU'

        with self.assertRaises(ParcoursDoctoralNonTrouveException):
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))

    def test_should_generer_exception_si_statut_parcours_doctoral_invalide(self):
        self.parcours_doctoral.statut = ChoixStatutParcoursDoctoral.ADMIS

        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))

        self.assertIsInstance(e.exception.exceptions.pop(), StatutDoctoratDifferentDefensePriveeAutoriseeException)

    def test_should_generer_exception_si_proces_verbal_non_specifie(self):
        defense_privee = self.defense_privee_repository.get(entity_id=self.defense_privee.entity_id)
        defense_privee.proces_verbal = []

        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))

        self.assertIsInstance(e.exception.exceptions.pop(), DefensePriveeNonCompleteePourDecisionException)

    def test_should_generer_exception_si_date_non_specifiee(self):
        defense_privee = self.defense_privee_repository.get(entity_id=self.defense_privee.entity_id)
        defense_privee.date_heure = None

        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))

        self.assertIsInstance(e.exception.exceptions.pop(), DefensePriveeNonCompleteePourDecisionException)

    def test_should_generer_exception_si_defense_privee_non_active(self):
        defense_privee = self.defense_privee_repository.get(entity_id=self.defense_privee.entity_id)
        defense_privee.est_active = False

        with self.assertRaises(DefensePriveeNonTrouveeException):
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))

    def test_should_changer_statut_parcours_doctoral_et_remplacer_defense_privee_active(self):
        self.parcours_doctoral.statut = ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_AUTORISEE

        resultat = self.message_bus.invoke(self.cmd(**self.parametres_cmd))

        self.assertEqual(resultat, self.parcours_doctoral.entity_id)
        self.assertEqual(self.parcours_doctoral.statut, ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_A_RECOMMENCER)

        defenses_privees = self.defense_privee_repository.search_dto(self.parcours_doctoral.entity_id)
        self.assertEqual(len(defenses_privees), 2)

        ancienne_defense_privee, nouvelle_defense_privee = (
            defenses_privees
            if defenses_privees[0].uuid == self.defense_privee.entity_id.uuid
            else defenses_privees[::-1]
        )
        self.assertFalse(ancienne_defense_privee.est_active)
        self.assertTrue(nouvelle_defense_privee.est_active)
