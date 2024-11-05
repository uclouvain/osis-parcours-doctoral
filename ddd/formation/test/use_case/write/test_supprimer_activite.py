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

from parcours_doctoral.ddd.formation.commands import SupprimerActiviteCommand
from parcours_doctoral.ddd.formation.domain.model.enums import CategorieActivite, StatutActivite
from parcours_doctoral.ddd.formation.domain.validator.exceptions import (
    ActiviteDejaSoumise,
    ActiviteNonTrouvee,
)
from parcours_doctoral.ddd.formation.test.factory.activite import ActiviteFactory
from parcours_doctoral.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from parcours_doctoral.infrastructure.parcours_doctoral.formation.repository.in_memory.activite import (
    ActiviteInMemoryRepository,
)


class SoumettreActivitesTestCase(TestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance

    def tearDown(self) -> None:
        ActiviteInMemoryRepository.reset()

    def test_pas_supprimer_activite_non_trouvee(self):
        with self.assertRaises(ActiviteNonTrouvee):
            self.message_bus.invoke(SupprimerActiviteCommand(activite_uuid="activite-inexistante"))

    def test_supprimer_activite(self):
        original_length = len(ActiviteInMemoryRepository.entities)
        self.message_bus.invoke(
            SupprimerActiviteCommand(activite_uuid=ActiviteInMemoryRepository.entities[0].entity_id.uuid)
        )
        self.assertEqual(original_length - 1, len(ActiviteInMemoryRepository.entities))

    def test_supprimer_sous_activite_si_parente_supprimee(self):
        parent_service = ActiviteFactory(
            categorie=CategorieActivite.SEMINAR,
            generate_dto__class='SeminarDTOFactory',
        )
        ActiviteInMemoryRepository.entities = [
            parent_service,
            ActiviteFactory(
                parent_id=parent_service.entity_id,
                categorie=CategorieActivite.COMMUNICATION,
            ),
        ]
        self.message_bus.invoke(SupprimerActiviteCommand(activite_uuid=parent_service.entity_id.uuid))
        self.assertEqual(len(ActiviteInMemoryRepository.entities), 0)

    def test_pas_supprimer_activite_si_soumise(self):
        conference = ActiviteFactory(categorie=CategorieActivite.CONFERENCE, statut=StatutActivite.SOUMISE)
        ActiviteInMemoryRepository.entities = [conference]
        with self.assertRaises(ActiviteDejaSoumise):
            self.message_bus.invoke(SupprimerActiviteCommand(activite_uuid=conference.entity_id.uuid))

    def test_pas_supprimer_activite_parente_si_enfant_soumise(self):
        parent_service = ActiviteFactory(categorie=CategorieActivite.SEMINAR)
        ActiviteInMemoryRepository.entities = [
            parent_service,
            ActiviteFactory(
                parent_id=parent_service.entity_id,
                categorie=CategorieActivite.COMMUNICATION,
                statut=StatutActivite.SOUMISE,
            ),
        ]
        with self.assertRaises(ActiviteDejaSoumise):
            self.message_bus.invoke(SupprimerActiviteCommand(activite_uuid=parent_service.entity_id.uuid))
