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

from django.test import TestCase

from parcours_doctoral.ddd.epreuve_confirmation.commands import (
    RecupererDerniereEpreuveConfirmationQuery,
)
from parcours_doctoral.ddd.epreuve_confirmation.dtos import EpreuveConfirmationDTO
from parcours_doctoral.ddd.epreuve_confirmation.validators.exceptions import (
    EpreuveConfirmationNonTrouveeException,
)
from parcours_doctoral.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)


class TestRecupererDerniereEpreuveConfirmation(TestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance

    def test_should_pas_trouver_si_parcours_doctoral_inconnu(self):
        with self.assertRaises(EpreuveConfirmationNonTrouveeException):
            self.message_bus.invoke(
                RecupererDerniereEpreuveConfirmationQuery(
                    parcours_doctoral_uuid='inconnu',
                )
            )

    def test_should_pas_trouver_si_parcours_doctoral_connu_sans_epreuve(self):
        with self.assertRaises(EpreuveConfirmationNonTrouveeException):
            self.message_bus.invoke(
                RecupererDerniereEpreuveConfirmationQuery(
                    parcours_doctoral_uuid='uuid-SC3DP-promoteur-refus-membre-deja-approuve',
                )
            )

    def test_should_retourner_epreuve_confirmation_si_parcours_doctoral_connu_avec_epreuves(self):
        epreuve_confirmation: EpreuveConfirmationDTO = self.message_bus.invoke(
            RecupererDerniereEpreuveConfirmationQuery(
                parcours_doctoral_uuid='uuid-SC3DP-promoteur-refus-membre-deja-approuve-refus',
            )
        )
        self.assertEqual(epreuve_confirmation.uuid, 'c10')
