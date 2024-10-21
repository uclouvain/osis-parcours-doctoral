# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from django.test import TestCase

from infrastructure.shared_kernel.personne_connue_ucl.in_memory.personne_connue_ucl import (
    PersonneConnueUclInMemoryTranslator,
)
from parcours_doctoral.ddd.builder.parcours_doctoral_identity import (
    ParcoursDoctoralIdentityBuilder,
)
from parcours_doctoral.ddd.commands import (
    IdentifierMembreCACommand,
    IdentifierPromoteurCommand,
)
from parcours_doctoral.ddd.domain.model.enums import ChoixEtatSignature
from parcours_doctoral.ddd.domain.validator.exceptions import (
    DejaMembreException,
    GroupeDeSupervisionNonTrouveException,
    GroupeSupervisionCompletPourPromoteursException,
    MembreSoitInterneSoitExterneException,
    PromoteurNonTrouveException,
)
from parcours_doctoral.ddd.test.factory.person import PersonneConnueUclDTOFactory
from parcours_doctoral.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from parcours_doctoral.infrastructure.parcours_doctoral.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)


class TestIdentifierPromoteurService(TestCase):
    def setUp(self) -> None:
        self.uuid_promoteur = '00987890'
        self.uuid_parcours_doctoral = 'uuid-SC3DP'
        PersonneConnueUclInMemoryTranslator.personnes_connues_ucl.add(
            PersonneConnueUclDTOFactory(matricule="0123456"),
        )

        self.groupe_de_supervision_repository = GroupeDeSupervisionInMemoryRepository()
        self.parcours_doctoral_id = ParcoursDoctoralIdentityBuilder.build_from_uuid(self.uuid_parcours_doctoral)

        self.message_bus = message_bus_in_memory_instance
        self.cmd = IdentifierPromoteurCommand(
            uuid_parcours_doctoral=self.uuid_parcours_doctoral,
            matricule_auteur="0123456",
            matricule=self.uuid_promoteur,
            prenom="",
            nom="",
            email="",
            est_docteur=False,
            institution="",
            ville="",
            pays="",
            langue="",
        )
        self.addCleanup(self.groupe_de_supervision_repository.reset)

    def test_should_ajouter_promoteur_dans_groupe_supervision(self):
        promoteur_id = self.message_bus.invoke(self.cmd)
        groupe = self.groupe_de_supervision_repository.get_by_parcours_doctoral_id(self.parcours_doctoral_id)
        signatures = groupe.signatures_promoteurs
        self.assertEqual(len(signatures), 1)
        self.assertEqual(signatures[0].promoteur_id, promoteur_id)
        self.assertEqual(signatures[0].etat, ChoixEtatSignature.NOT_INVITED)

    def test_should_ajouter_promoteur_externe_dans_groupe_supervision(self):
        cmd = IdentifierPromoteurCommand(
            uuid_parcours_doctoral=self.uuid_parcours_doctoral,
            matricule="",
            matricule_auteur="0123456",
            prenom="John",
            nom="Doe",
            email="john@example.org",
            est_docteur=True,
            institution="Psy",
            ville="Labah",
            pays="FR",
            langue="fr-be",
        )
        # Add once
        self.message_bus.invoke(cmd)
        # Add twice
        with self.assertRaises(DejaMembreException):
            self.message_bus.invoke(cmd)

    def test_should_pas_ajouter_promoteur_externe_si_incomplet(self):
        cmd = IdentifierPromoteurCommand(
            uuid_parcours_doctoral=self.uuid_parcours_doctoral,
            matricule="",
            matricule_auteur="0123456",
            prenom="",
            nom="",
            email="john@example.org",
            est_docteur=False,
            institution="Psy",
            ville="Labah",
            pays="FR",
            langue="",
        )
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), MembreSoitInterneSoitExterneException)

    def test_should_pas_ajouter_promoteur_externe_si_interne_externe(self):
        cmd = IdentifierPromoteurCommand(
            uuid_parcours_doctoral=self.uuid_parcours_doctoral,
            matricule="012314984621",
            matricule_auteur="0123456",
            prenom="",
            nom="",
            email="john@example.org",
            est_docteur=False,
            institution="Psy",
            ville="Labah",
            pays="FR",
            langue="",
        )
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), MembreSoitInterneSoitExterneException)

    def test_should_pas_ajouter_personne_si_pas_promoteur(self):
        cmd = attr.evolve(self.cmd, matricule='paspromoteur')
        with self.assertRaises(PromoteurNonTrouveException):
            self.message_bus.invoke(cmd)

    def test_should_pas_ajouter_personne_si_deja_promoteur(self):
        self.message_bus.invoke(self.cmd)
        with self.assertRaises(DejaMembreException):
            self.message_bus.invoke(self.cmd)

    def test_should_pas_ajouter_personne_si_deja_membre_CA(self):
        self.message_bus.invoke(
            IdentifierMembreCACommand(
                uuid_parcours_doctoral=self.uuid_parcours_doctoral,
                matricule=self.uuid_promoteur,
                matricule_auteur="0123456",
                prenom="",
                nom="",
                email="",
                est_docteur=False,
                institution="",
                ville="",
                pays="",
                langue="",
            )
        )
        with self.assertRaises(DejaMembreException):
            self.message_bus.invoke(self.cmd)

    def test_should_pas_ajouter_si_groupe_parcours_doctoral_non_trouve(self):
        cmd = attr.evolve(self.cmd, uuid_parcours_doctoral='parcours_doctoralinconnue')
        with self.assertRaises(GroupeDeSupervisionNonTrouveException):
            self.message_bus.invoke(cmd)

    def test_should_pas_ajouter_personne_si_groupe_complet_pour_promoteurs(self):
        # Add 3 promoters -> valid
        for k in range(1, 4):
            self.message_bus.invoke(
                IdentifierPromoteurCommand(
                    uuid_parcours_doctoral=self.uuid_parcours_doctoral,
                    matricule='0098789{}'.format(k),
                    matricule_auteur="0123456",
                    prenom="",
                    nom="",
                    email="",
                    est_docteur=False,
                    institution="",
                    ville="",
                    pays="",
                    langue="",
                )
            )
        # Add a 4th promoter -> invalid
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd)
        self.assertIsInstance(e.exception.exceptions.pop(), GroupeSupervisionCompletPourPromoteursException)
