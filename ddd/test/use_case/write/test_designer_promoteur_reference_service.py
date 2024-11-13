# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################

import attr
from django.test import TestCase

from parcours_doctoral.ddd.builder.parcours_doctoral_identity import ParcoursDoctoralIdentityBuilder
from parcours_doctoral.ddd.commands import DesignerPromoteurReferenceCommand
from parcours_doctoral.ddd.domain.validator.exceptions import (
    ParcoursDoctoralNonTrouveException,
    SignataireNonTrouveException,
)
from parcours_doctoral.ddd.test.factory.person import PersonneConnueUclDTOFactory
from parcours_doctoral.infrastructure.parcours_doctoral.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from parcours_doctoral.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from infrastructure.shared_kernel.personne_connue_ucl.in_memory.personne_connue_ucl import \
    PersonneConnueUclInMemoryTranslator


class TestDesignerPromoteurDeReferenceService(TestCase):
    def setUp(self) -> None:
        self.uuid_promoteur = 'promoteur-SC3DP'
        self.uuid_parcours_doctoral = 'uuid-SC3DP-sans-promoteur-reference'
        PersonneConnueUclInMemoryTranslator.personnes_connues_ucl.add(
            PersonneConnueUclDTOFactory(matricule="0123456"),
        )

        self.groupe_de_supervision_repository = GroupeDeSupervisionInMemoryRepository()
        self.parcours_doctoral_id = ParcoursDoctoralIdentityBuilder.build_from_uuid(self.uuid_parcours_doctoral)

        self.message_bus = message_bus_in_memory_instance
        self.cmd = DesignerPromoteurReferenceCommand(
            uuid_parcours_doctoral=self.uuid_parcours_doctoral,
            uuid_promoteur=self.uuid_promoteur,
            matricule_auteur="0123456",
        )
        self.addCleanup(self.groupe_de_supervision_repository.reset)

    def test_should_designer_promoteur_reference(self):
        groupe = self.groupe_de_supervision_repository.get_by_parcours_doctoral_id(self.parcours_doctoral_id)
        self.assertIsNone(groupe.promoteur_reference_id)

        parcours_doctoral_id = self.message_bus.invoke(self.cmd)
        self.assertEqual(parcours_doctoral_id.uuid, self.uuid_parcours_doctoral)
        groupe = self.groupe_de_supervision_repository.get_by_parcours_doctoral_id(parcours_doctoral_id)
        self.assertEqual(groupe.promoteur_reference_id.uuid, self.uuid_promoteur)

    def test_should_changer_promoteur_reference(self):
        uuid_parcours_doctoral = "uuid-SC3DP-promoteur-deja-approuve"
        groupe = self.groupe_de_supervision_repository.get_by_parcours_doctoral_id(
            ParcoursDoctoralIdentityBuilder.build_from_uuid(uuid_parcours_doctoral)
        )
        self.assertEqual(groupe.promoteur_reference_id.uuid, "promoteur-SC3DP")

        parcours_doctoral_id = self.message_bus.invoke(
            DesignerPromoteurReferenceCommand(
                uuid_parcours_doctoral=uuid_parcours_doctoral,
                uuid_promoteur="promoteur-SC3DP-deja-approuve",
                matricule_auteur="0123456",
            )
        )
        self.assertEqual(parcours_doctoral_id.uuid, uuid_parcours_doctoral)
        groupe = self.groupe_de_supervision_repository.get_by_parcours_doctoral_id(parcours_doctoral_id)
        self.assertEqual(groupe.promoteur_reference_id.uuid, "promoteur-SC3DP-deja-approuve")

    def test_should_pas_designer_personne_si_pas_promoteur(self):
        cmd = attr.evolve(self.cmd, uuid_promoteur='paspromoteur')
        with self.assertRaises(SignataireNonTrouveException):
            self.message_bus.invoke(cmd)

    def test_should_pas_designer_si_groupe_parcours_doctoral_non_trouve(self):
        cmd = attr.evolve(self.cmd, uuid_parcours_doctoral='parcours_doctoralinconnue')
        with self.assertRaises(ParcoursDoctoralNonTrouveException):
            self.message_bus.invoke(cmd)
