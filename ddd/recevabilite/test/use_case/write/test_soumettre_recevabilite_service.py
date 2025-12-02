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
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.recevabilite.commands import SoumettreRecevabiliteCommand
from parcours_doctoral.ddd.recevabilite.test.factory.recevabilite import (
    RecevabiliteFactory,
)
from parcours_doctoral.ddd.recevabilite.validators.exceptions import (
    EtapeRecevabilitePasEnCoursException,
    RecevabiliteNonCompleteeException,
)
from parcours_doctoral.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from parcours_doctoral.infrastructure.parcours_doctoral.recevabilite.repository.in_memory.recevabilite import (
    RecevabiliteInMemoryRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.repository.in_memory.parcours_doctoral import (
    ParcoursDoctoralInMemoryRepository,
)


class TestSoumettreRecevabilite(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cmd = SoumettreRecevabiliteCommand
        cls.message_bus = message_bus_in_memory_instance
        cls.recevabilite_repository = RecevabiliteInMemoryRepository()
        cls.parcours_doctoral_repository = ParcoursDoctoralInMemoryRepository()

    def setUp(self):
        self.addCleanup(RecevabiliteInMemoryRepository.reset)
        self.addCleanup(ParcoursDoctoralInMemoryRepository.reset)
        self.parcours_doctoral = self.parcours_doctoral_repository.entities[0]
        self.parcours_doctoral_identity = self.parcours_doctoral.entity_id
        self.parcours_doctoral.statut = ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE
        self.parametres_cmd = {
            'parcours_doctoral_uuid': self.parcours_doctoral_identity.uuid,
            'matricule_auteur': '1234',
            'titre_these': 'Titre',
            'date_decision': datetime.date(2022, 1, 1),
            'date_envoi_manuscrit': datetime.date(2023, 1, 1),
        }

    def test_should_generer_exception_si_donnees_manquantes(self):
        self.parametres_cmd['titre_these'] = ''

        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))
        self.assertIsInstance(e.exception.exceptions.pop(), RecevabiliteNonCompleteeException)

    def test_should_generer_exception_si_statut_parcours_doctoral_incorrect(self):
        self.parcours_doctoral.statut = ChoixStatutParcoursDoctoral.RECEVABILITE_REUSSIE

        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))
        self.assertIsInstance(e.exception.exceptions.pop(), EtapeRecevabilitePasEnCoursException)

    def test_should_soumettre_recevabilite_si_valide_et_pour_premiere_fois(self):
        parcours_doctoral_id_resultat = self.message_bus.invoke(self.cmd(**self.parametres_cmd))

        recevabilite_mise_a_jour = RecevabiliteInMemoryRepository.get_active(
            parcours_doctoral_entity_id=self.parcours_doctoral_identity,
        )

        parcours_doctoral = ParcoursDoctoralInMemoryRepository.get(self.parcours_doctoral_identity)

        self.assertEqual(recevabilite_mise_a_jour.parcours_doctoral_id, parcours_doctoral_id_resultat)
        self.assertEqual(recevabilite_mise_a_jour.date_decision, self.parametres_cmd['date_decision'])
        self.assertEqual(recevabilite_mise_a_jour.date_envoi_manuscrit, self.parametres_cmd['date_envoi_manuscrit'])

        self.assertEqual(parcours_doctoral.statut, ChoixStatutParcoursDoctoral.RECEVABILITE_SOUMISE)
        self.assertEqual(parcours_doctoral.titre_these_propose, self.parametres_cmd['titre_these'])

    def test_should_soumettre_recevabilite_si_valide_et_pour_une_mise_a_jour(self):
        recevabilite = RecevabiliteFactory(
            parcours_doctoral_id=self.parcours_doctoral_repository.entities[0].entity_id,
        )
        self.recevabilite_repository.save(recevabilite)

        parcours_doctoral_id_resultat = self.message_bus.invoke(self.cmd(**self.parametres_cmd))

        recevabilite_mise_a_jour = self.recevabilite_repository.get(entity_id=recevabilite.entity_id)

        parcours_doctoral = ParcoursDoctoralInMemoryRepository.get(self.parcours_doctoral_identity)

        self.assertEqual(recevabilite_mise_a_jour.parcours_doctoral_id, parcours_doctoral_id_resultat)
        self.assertEqual(recevabilite_mise_a_jour.date_decision, self.parametres_cmd['date_decision'])
        self.assertEqual(recevabilite_mise_a_jour.date_envoi_manuscrit, self.parametres_cmd['date_envoi_manuscrit'])

        self.assertEqual(parcours_doctoral.statut, ChoixStatutParcoursDoctoral.RECEVABILITE_SOUMISE)
        self.assertEqual(parcours_doctoral.titre_these_propose, self.parametres_cmd['titre_these'])
