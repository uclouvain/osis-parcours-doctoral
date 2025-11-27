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
from parcours_doctoral.ddd.defense_privee.commands import SoumettreDefensePriveeCommand
from parcours_doctoral.ddd.defense_privee.test.factory.defense_privee import (
    DefensePriveeFactory,
)
from parcours_doctoral.ddd.defense_privee.validators.exceptions import (
    DefensePriveeNonCompleteeException,
)
from parcours_doctoral.ddd.defense_privee_soutenance_publique.commands import \
    SoumettreDefensePriveeEtSoutenancePubliqueCommand
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.soutenance_publique.validators.exceptions import SoutenancePubliqueNonCompleteeException, \
    EtapeSoutenancePubliquePasEnCoursException
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


class TestSoumettreDefensePriveeSoutenancePublique(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cmd = SoumettreDefensePriveeEtSoutenancePubliqueCommand
        cls.message_bus = message_bus_in_memory_instance
        cls.defense_privee_repository = DefensePriveeInMemoryRepository()
        cls.parcours_doctoral_repository = ParcoursDoctoralInMemoryRepository()

    def setUp(self):
        self.addCleanup(DefensePriveeInMemoryRepository.reset)
        self.addCleanup(ParcoursDoctoralInMemoryRepository.reset)
        self.parcours_doctoral = self.parcours_doctoral_repository.entities[0]
        self.parcours_doctoral.statut = ChoixStatutParcoursDoctoral.RECEVABILITE_REUSSIE
        self.defense_privee = DefensePriveeFactory(parcours_doctoral_id=self.parcours_doctoral.entity_id)
        self.defense_privee_repository.save(self.defense_privee)
        self.parametres_cmd = {
            'uuid_parcours_doctoral': self.parcours_doctoral.entity_id.uuid,
            'matricule_auteur': '1234',
            'titre_these': 'Titre defense',
            'langue_soutenance_publique': 'FR',
            'date_heure_defense_privee': datetime.datetime(2022, 1, 1),
            'lieu_defense_privee': 'Lieu défense privée',
            'date_envoi_manuscrit': datetime.date(2023, 1, 1),
            'date_heure_soutenance_publique': datetime.datetime(2022, 1, 2),
            'lieu_soutenance_publique': 'Lieu soutenance publique',
            'local_deliberation': 'Local délibération',
            'resume_annonce': 'Résumé annonce',
            'photo_annonce': ['uuid-photo-annonce'],
        }

    def test_should_generer_exception_si_donnees_manquantes(self):
        parametres = {
            **self.parametres_cmd,
            'date_heure_defense_privee': None,
        }

        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**parametres))
        self.assertIsInstance(e.exception.exceptions.pop(), DefensePriveeNonCompleteeException)

        parametres = {
            **self.parametres_cmd,
            'titre_these': '',
        }

        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**parametres))
        self.assertIsInstance(e.exception.exceptions.pop(), DefensePriveeNonCompleteeException)

        parametres = {
            **self.parametres_cmd,
            'langue_soutenance_publique': '',
        }

        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**parametres))
        self.assertIsInstance(e.exception.exceptions.pop(), SoutenancePubliqueNonCompleteeException)

        parametres = {
            **self.parametres_cmd,
            'date_heure_soutenance_publique': None,
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

    def test_should_soumettre_defense_privee_et_soutenance_publique_si_valide(self):
        parcours_doctoral_id_resultat = self.message_bus.invoke(self.cmd(**self.parametres_cmd))

        defense_privee_mise_a_jour = defense_privee.DefensePriveeInMemoryRepository.get(
            entity_id=self.defense_privee.entity_id,
        )

        parcours_doctoral = ParcoursDoctoralInMemoryRepository.get(defense_privee_mise_a_jour.parcours_doctoral_id)

        self.assertEqual(defense_privee_mise_a_jour.parcours_doctoral_id, parcours_doctoral_id_resultat)
        self.assertEqual(defense_privee_mise_a_jour.date_heure, self.parametres_cmd['date_heure_defense_privee'])
        self.assertEqual(defense_privee_mise_a_jour.lieu, self.parametres_cmd['lieu_defense_privee'])
        self.assertEqual(defense_privee_mise_a_jour.date_envoi_manuscrit, self.parametres_cmd['date_envoi_manuscrit'])

        self.assertEqual(parcours_doctoral.statut, ChoixStatutParcoursDoctoral.SOUTENANCE_PUBLIQUE_SOUMISE)
        self.assertEqual(parcours_doctoral.titre_these_propose, self.parametres_cmd['titre_these'])
        self.assertEqual(parcours_doctoral.langue_soutenance_publique, self.parametres_cmd['langue_soutenance_publique'],)
        self.assertEqual(parcours_doctoral.date_heure_soutenance_publique, self.parametres_cmd['date_heure_soutenance_publique'],)
        self.assertEqual(parcours_doctoral.lieu_soutenance_publique, self.parametres_cmd['lieu_soutenance_publique'])
        self.assertEqual(parcours_doctoral.local_deliberation, self.parametres_cmd['local_deliberation'])
        self.assertEqual(parcours_doctoral.resume_annonce, self.parametres_cmd['resume_annonce'])
        self.assertEqual(parcours_doctoral.photo_annonce, self.parametres_cmd['photo_annonce'])
