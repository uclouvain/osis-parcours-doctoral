# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from parcours_doctoral.ddd.defense_privee.builder.defense_privee_identity import (
    DefensePriveeIdentityBuilder,
)
from parcours_doctoral.ddd.defense_privee.commands import (
    ModifierDefensePriveeParCDDCommand,
)
from parcours_doctoral.ddd.defense_privee.validators.exceptions import (
    DefensePriveeNonTrouveeException,
)
from parcours_doctoral.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from parcours_doctoral.infrastructure.parcours_doctoral.defense_privee.repository.in_memory import (
    defense_privee,
)


class TestModifierDefensePriveeParCDD(TestCase):
    def setUp(self):
        self.message_bus = message_bus_in_memory_instance

    def test_should_pas_trouver_si_defense_privee_inconnue(self):
        with self.assertRaises(DefensePriveeNonTrouveeException):
            self.message_bus.invoke(
                ModifierDefensePriveeParCDDCommand(
                    uuid='inconnue',
                    date_limite=datetime.date(2022, 7, 1),
                    rapport_recherche=['mon_fichier_1'],
                    proces_verbal_ca=['mon_fichier_2'],
                    avis_renouvellement_mandat_recherche=['mon_fichier_3'],
                    date=datetime.date(2022, 4, 1),
                )
            )

    def test_should_modifier_defense_privee_connue(self):
        defense_privee_id = DefensePriveeIdentityBuilder.build_from_uuid('c2')

        defense_privee_id_resultat = self.message_bus.invoke(
            ModifierDefensePriveeParCDDCommand(
                uuid='c2',
                date_limite=datetime.date(2022, 7, 1),
                rapport_recherche=['mon_fichier_1'],
                proces_verbal_ca=['mon_fichier_2'],
                avis_renouvellement_mandat_recherche=['mon_fichier_3'],
                date=datetime.date(2022, 4, 1),
            )
        )

        defense_privee_mise_a_jour = defense_privee.DefensePriveeInMemoryRepository.get(
            entity_id=defense_privee_id,
        )

        self.assertEqual(defense_privee_id, defense_privee_id_resultat)
        self.assertEqual(defense_privee_mise_a_jour.date, datetime.date(2022, 4, 1))
        self.assertEqual(defense_privee_mise_a_jour.date_limite, datetime.date(2022, 7, 1))
        self.assertEqual(defense_privee_mise_a_jour.rapport_recherche, ['mon_fichier_1'])
        self.assertEqual(defense_privee_mise_a_jour.proces_verbal_ca, ['mon_fichier_2'])
        self.assertEqual(defense_privee_mise_a_jour.avis_renouvellement_mandat_recherche, ['mon_fichier_3'])
