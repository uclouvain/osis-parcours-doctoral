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

from django.test import TestCase

from parcours_doctoral.ddd.commands import RecupererParcoursDoctoralQuery
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.domain.validator.exceptions import (
    ParcoursDoctoralNonTrouveException,
)
from parcours_doctoral.ddd.dtos import ParcoursDoctoralDTO
from parcours_doctoral.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)


class TestRecupererDoctorat(TestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance

    def test_should_pas_trouver_si_parcours_doctoral_inconnu(self):
        with self.assertRaises(ParcoursDoctoralNonTrouveException):
            self.message_bus.invoke(
                RecupererParcoursDoctoralQuery(
                    parcours_doctoral_uuid='inconnu',
                )
            )

    def test_should_recuperer_parcours_doctoral_connu(self):
        parcours_doctoral_dto: ParcoursDoctoralDTO = self.message_bus.invoke(
            RecupererParcoursDoctoralQuery(
                parcours_doctoral_uuid='uuid-SC3DP-promoteurs-membres-deja-approuves',
            )
        )
        self.assertEqual(parcours_doctoral_dto.uuid, 'uuid-SC3DP-promoteurs-membres-deja-approuves')
        self.assertEqual(parcours_doctoral_dto.reference, 'r4')

        self.assertEqual(parcours_doctoral_dto.statut, ChoixStatutParcoursDoctoral.ADMITTED.name)

        self.assertEqual(parcours_doctoral_dto.formation.sigle, 'SC3DP')
        self.assertEqual(parcours_doctoral_dto.formation.annee, 2022)
        self.assertEqual(parcours_doctoral_dto.formation.intitule, 'Doctorat en sciences')

        self.assertEqual(parcours_doctoral_dto.matricule_doctorant, '3')
        self.assertEqual(parcours_doctoral_dto.nom_doctorant, 'Dupond'),
        self.assertEqual(parcours_doctoral_dto.prenom_doctorant, 'Pierre')
