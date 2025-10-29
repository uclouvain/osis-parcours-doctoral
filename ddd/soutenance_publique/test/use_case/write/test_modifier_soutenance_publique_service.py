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

from parcours_doctoral.ddd.domain.validator.exceptions import (
    ParcoursDoctoralNonTrouveException,
)
from parcours_doctoral.ddd.soutenance_publique.commands import (
    ModifierSoutenancePubliqueCommand,
)
from parcours_doctoral.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from parcours_doctoral.infrastructure.parcours_doctoral.repository.in_memory.parcours_doctoral import (
    ParcoursDoctoralInMemoryRepository,
)


class TestModifierSoutenancePublique(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cmd = ModifierSoutenancePubliqueCommand
        cls.message_bus = message_bus_in_memory_instance
        cls.parcours_doctoral_repository = ParcoursDoctoralInMemoryRepository()

    def setUp(self):
        self.addCleanup(ParcoursDoctoralInMemoryRepository.reset)
        self.parcours_doctoral_id = ParcoursDoctoralInMemoryRepository.entities[0].entity_id
        self.parametres_cmd = {
            'uuid_parcours_doctoral': self.parcours_doctoral_id.uuid,
            'matricule_auteur': '1234',
            'langue': 'FR',
            'date_heure': datetime.datetime(2025, 10, 1, 11, 30),
            'lieu': 'Louvain-La-Neuve',
            'local_deliberation': 'D1',
            'informations_complementaires': 'Informations',
            'resume_annonce': 'Resumé',
            'photo_annonce': ['uuid-photo'],
            'proces_verbal': ['uuid-proces-verbal'],
            'date_retrait_diplome': datetime.date(2025, 11, 1),
        }

    def test_should_generer_exception_si_parcours_doctoral_inconnu(self):
        self.parametres_cmd['uuid_parcours_doctoral'] = 'INCONNU'
        with self.assertRaises(ParcoursDoctoralNonTrouveException) as e:
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))

    def test_should_modifier_parcours_doctoral(self):
        resultat = self.message_bus.invoke(self.cmd(**self.parametres_cmd))

        proposition = self.parcours_doctoral_repository.get(entity_id=self.parcours_doctoral_id)

        self.assertEqual(resultat, proposition.entity_id)

        self.assertEqual(proposition.langue_soutenance_publique, self.parametres_cmd['langue'])
        self.assertEqual(proposition.date_heure_soutenance_publique, self.parametres_cmd['date_heure'])
        self.assertEqual(proposition.lieu_soutenance_publique, self.parametres_cmd['lieu'])
        self.assertEqual(proposition.local_deliberation, self.parametres_cmd['local_deliberation'])
        self.assertEqual(
            proposition.informations_complementaires_soutenance_publique,
            self.parametres_cmd['informations_complementaires'],
        )
        self.assertEqual(proposition.resume_annonce, self.parametres_cmd['resume_annonce'])
        self.assertEqual(proposition.photo_annonce, self.parametres_cmd['photo_annonce'])
        self.assertEqual(proposition.proces_verbal_soutenance_publique, self.parametres_cmd['proces_verbal'])
        self.assertEqual(proposition.date_retrait_diplome, self.parametres_cmd['date_retrait_diplome'])
