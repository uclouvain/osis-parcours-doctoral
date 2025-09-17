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

from django.test import SimpleTestCase

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from parcours_doctoral.ddd.domain.model.enums import (
    ChoixLangueDefense,
    ChoixStatutParcoursDoctoral,
)
from parcours_doctoral.ddd.soutenance_publique.commands import (
    SoumettreSoutenancePubliqueCommand,
)
from parcours_doctoral.ddd.soutenance_publique.validators.exceptions import (
    EtapeSoutenancePubliquePasEnCoursException,
    SoutenancePubliqueNonCompleteeException,
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


class TestSoumettreSoutenancePublique(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cmd = SoumettreSoutenancePubliqueCommand
        cls.message_bus = message_bus_in_memory_instance
        cls.parcours_doctoral_repository = ParcoursDoctoralInMemoryRepository()

    def setUp(self):
        self.addCleanup(DefensePriveeInMemoryRepository.reset)
        self.addCleanup(ParcoursDoctoralInMemoryRepository.reset)
        self.parcours_doctoral = ParcoursDoctoralInMemoryRepository.entities[0]
        self.parcours_doctoral.statut = ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_REUSSIE
        self.parametres_cmd = {
            'uuid_parcours_doctoral': self.parcours_doctoral.entity_id.uuid,
            'matricule_auteur': '1234',
            'langue': ChoixLangueDefense.FRENCH.name,
            'autre_langue': 'Japonais',
            'date_heure': datetime.datetime(2025, 1, 5, 11, 30),
            'lieu': 'UCLouvain',
            'local_deliberation': 'D1',
            'resume_annonce': 'Résumé',
            'photo_annonce': ['uuid-fichier'],
        }

    def test_should_generer_exception_si_donnees_manquantes(self):
        parametres = {
            **self.parametres_cmd,
            'langue': '',
        }

        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**parametres))
        self.assertIsInstance(e.exception.exceptions.pop(), SoutenancePubliqueNonCompleteeException)

        parametres = {
            **self.parametres_cmd,
            'date_heure': None,
        }

        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**parametres))
        self.assertIsInstance(e.exception.exceptions.pop(), SoutenancePubliqueNonCompleteeException)

        parametres = {
            **self.parametres_cmd,
            'photo_annonce': [],
        }

        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**parametres))
        self.assertIsInstance(e.exception.exceptions.pop(), SoutenancePubliqueNonCompleteeException)

    def test_should_generer_exception_si_statut_doctorat_incorrect(self):
        self.parcours_doctoral.statut = ChoixStatutParcoursDoctoral.ADMIS

        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))
        self.assertIsInstance(e.exception.exceptions.pop(), EtapeSoutenancePubliquePasEnCoursException)

    def test_should_soumettre_soutenance_publique_si_valide(self):
        parcours_doctoral_id_resultat = self.message_bus.invoke(self.cmd(**self.parametres_cmd))

        parcours_doctoral = ParcoursDoctoralInMemoryRepository.get(self.parcours_doctoral.entity_id)

        self.assertEqual(parcours_doctoral_id_resultat, self.parcours_doctoral.entity_id)

        self.assertEqual(parcours_doctoral.statut, ChoixStatutParcoursDoctoral.SOUTENANCE_PUBLIQUE_SOUMISE)

        self.assertEqual(
            parcours_doctoral.langue_soutenance_publique,
            ChoixLangueDefense[self.parametres_cmd['langue']],
        )
        self.assertEqual(parcours_doctoral.autre_langue_soutenance_publique, self.parametres_cmd['autre_langue'])
        self.assertEqual(parcours_doctoral.date_heure_soutenance_publique, self.parametres_cmd['date_heure'])
        self.assertEqual(parcours_doctoral.lieu_soutenance_publique, self.parametres_cmd['lieu'])
        self.assertEqual(parcours_doctoral.local_deliberation, self.parametres_cmd['local_deliberation'])
        self.assertEqual(parcours_doctoral.resume_annonce, self.parametres_cmd['resume_annonce'])
        self.assertEqual(parcours_doctoral.photo_annonce, self.parametres_cmd['photo_annonce'])
