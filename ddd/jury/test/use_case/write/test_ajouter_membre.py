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
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from django.test import TestCase

from parcours_doctoral.ddd.jury.commands import AjouterMembreCommand
from parcours_doctoral.ddd.jury.domain.model.enums import RoleJury
from parcours_doctoral.ddd.jury.test.factory.jury import MembreJuryFactory
from parcours_doctoral.ddd.jury.validator.exceptions import (
    MembreDejaDansJuryException,
    MembreExterneSansEmailException,
    MembreExterneSansGenreException,
    MembreExterneSansInstitutionException,
    MembreExterneSansNomException,
    MembreExterneSansPaysException,
    MembreExterneSansPrenomException,
    MembreExterneSansTitreException,
    NonDocteurSansJustificationException,
)
from parcours_doctoral.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from parcours_doctoral.infrastructure.parcours_doctoral.jury.repository.in_memory.jury import (
    JuryInMemoryRepository,
)


class TestAjouterMembre(TestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance

    def tearDown(self) -> None:
        JuryInMemoryRepository.reset()

    def test_should_ajouter_membre_matricule_deja_existant(self):
        JuryInMemoryRepository.entities[0].membres.append(
            MembreJuryFactory(uuid='uuid-matricule', matricule='matricule')
        )
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(
                AjouterMembreCommand(
                    uuid_jury='uuid-jury',
                    matricule='matricule',
                    institution='UCLouvain',
                    autre_institution='autre',
                    pays='pays',
                    nom='nom',
                    prenom='prenom',
                    titre=None,
                    justification_non_docteur=None,
                    genre=None,
                    email='email',
                )
            )
            self.assertIsInstance(context.exception.exceptions.pop(), MembreDejaDansJuryException)

    def test_should_ajouter_membre_externe(self):
        self.message_bus.invoke(
            AjouterMembreCommand(
                uuid_jury='uuid-jury',
                matricule=None,
                institution='institution foo',
                autre_institution='autre',
                pays='pays',
                nom='nom',
                prenom='prenom',
                titre='DOCTEUR',
                justification_non_docteur=None,
                genre='FEMININ',
                email='email',
            )
        )

        jury = JuryInMemoryRepository.entities[0]
        self.assertEqual(len(jury.membres), 3)
        membre = jury.membres[-1]
        self.assertIsNotNone(membre.uuid)
        self.assertIsNone(membre.matricule)
        self.assertIs(membre.est_promoteur, False)
        self.assertEqual(membre.institution, 'institution foo')
        self.assertEqual(membre.autre_institution, 'autre')
        self.assertEqual(membre.pays, 'pays')
        self.assertEqual(membre.nom, 'nom')
        self.assertEqual(membre.prenom, 'prenom')
        self.assertEqual(membre.titre, 'DOCTEUR')
        self.assertIsNone(membre.justification_non_docteur)
        self.assertEqual(membre.genre, 'FEMININ')
        self.assertEqual(membre.email, 'email')
        self.assertEqual(membre.role, RoleJury.MEMBRE.name)

    def test_should_ajouter_membre_externe_email_exception(self):
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(
                AjouterMembreCommand(
                    uuid_jury='uuid-jury',
                    matricule=None,
                    institution='institution foo',
                    autre_institution='autre',
                    pays='pays',
                    nom='nom',
                    prenom='prenom',
                    titre='DOCTEUR',
                    justification_non_docteur=None,
                    genre='FEMININ',
                    email='',
                )
            )
            self.assertIsInstance(context.exception.exceptions.pop(), MembreExterneSansEmailException)

    def test_should_ajouter_membre_externe_genre_exception(self):
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(
                AjouterMembreCommand(
                    uuid_jury='uuid-jury',
                    matricule=None,
                    institution='institution foo',
                    autre_institution='autre',
                    pays='pays',
                    nom='nom',
                    prenom='prenom',
                    titre='DOCTEUR',
                    justification_non_docteur=None,
                    genre='',
                    email='email',
                )
            )
            self.assertIsInstance(context.exception.exceptions.pop(), MembreExterneSansGenreException)

    def test_should_ajouter_membre_externe_institution_exception(self):
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(
                AjouterMembreCommand(
                    uuid_jury='uuid-jury',
                    matricule=None,
                    institution='',
                    autre_institution='autre',
                    pays='pays',
                    nom='nom',
                    prenom='prenom',
                    titre='DOCTEUR',
                    justification_non_docteur=None,
                    genre='FEMININ',
                    email='email',
                )
            )
            self.assertIsInstance(context.exception.exceptions.pop(), MembreExterneSansInstitutionException)

    def test_should_ajouter_membre_externe_nom_exception(self):
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(
                AjouterMembreCommand(
                    uuid_jury='uuid-jury',
                    matricule=None,
                    institution='institution foo',
                    autre_institution='autre',
                    pays='pays',
                    nom='',
                    prenom='prenom',
                    titre='DOCTEUR',
                    justification_non_docteur=None,
                    genre='FEMININ',
                    email='email',
                )
            )
            self.assertIsInstance(context.exception.exceptions.pop(), MembreExterneSansNomException)

    def test_should_ajouter_membre_externe_pays_exception(self):
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(
                AjouterMembreCommand(
                    uuid_jury='uuid-jury',
                    matricule=None,
                    institution='institution foo',
                    autre_institution='autre',
                    pays='',
                    nom='nom',
                    prenom='prenom',
                    titre='DOCTEUR',
                    justification_non_docteur=None,
                    genre='FEMININ',
                    email='email',
                )
            )
            self.assertIsInstance(context.exception.exceptions.pop(), MembreExterneSansPaysException)

    def test_should_ajouter_membre_externe_prenom_exception(self):
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(
                AjouterMembreCommand(
                    uuid_jury='uuid-jury',
                    matricule=None,
                    institution='institution foo',
                    autre_institution='autre',
                    pays='pays',
                    nom='nom',
                    prenom='',
                    titre='DOCTEUR',
                    justification_non_docteur=None,
                    genre='FEMININ',
                    email='email',
                )
            )
            self.assertIsInstance(context.exception.exceptions.pop(), MembreExterneSansPrenomException)

    def test_should_ajouter_membre_externe_titre_exception(self):
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(
                AjouterMembreCommand(
                    uuid_jury='uuid-jury',
                    matricule=None,
                    institution='institution foo',
                    autre_institution='autre',
                    pays='pays',
                    nom='nom',
                    prenom='prenom',
                    titre='',
                    justification_non_docteur=None,
                    genre='FEMININ',
                    email='email',
                )
            )
            self.assertIsInstance(context.exception.exceptions.pop(), MembreExterneSansTitreException)

    def test_should_ajouter_membre_externe_justification_exception(self):
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(
                AjouterMembreCommand(
                    uuid_jury='uuid-jury',
                    matricule=None,
                    institution='institution foo',
                    autre_institution='autre',
                    pays='pays',
                    nom='nom',
                    prenom='prenom',
                    titre='NON_DOCTEUR',
                    justification_non_docteur='',
                    genre='FEMININ',
                    email='email',
                )
            )
            self.assertIsInstance(context.exception.exceptions.pop(), NonDocteurSansJustificationException)
