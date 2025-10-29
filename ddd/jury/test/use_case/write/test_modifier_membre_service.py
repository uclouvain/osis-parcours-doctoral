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
from django.test import SimpleTestCase

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from parcours_doctoral.ddd.jury.commands import ModifierMembreCommand
from parcours_doctoral.ddd.jury.domain.model.jury import JuryIdentity
from parcours_doctoral.ddd.jury.domain.validator.exceptions import (
    JuryNonTrouveException,
    MembreNonTrouveDansJuryException,
    PromoteurModifieException,
)
from parcours_doctoral.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from parcours_doctoral.infrastructure.parcours_doctoral.jury.repository.in_memory.jury import (
    JuryInMemoryRepository,
)


class TestModifierMembre(SimpleTestCase):
    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance

    def tearDown(self) -> None:
        JuryInMemoryRepository.reset()

    def test_should_modifier_membre(self):
        self.message_bus.invoke(
            ModifierMembreCommand(
                uuid_jury='uuid-jury',
                uuid_membre='uuid-membre',
                matricule=None,
                institution='une_autre_institution',
                autre_institution=None,
                pays='autre_pays',
                nom='autre_nom',
                prenom='autre_prenom',
                titre='PROFESSEUR',
                justification_non_docteur=None,
                genre='FEMININ',
                email='autre_email',
                langue='FR',
            )
        )

        jury = JuryInMemoryRepository.get(JuryIdentity(uuid='uuid-jury'))
        self.assertEqual(len(jury.membres), 2)
        membre = jury.membres[-1]
        self.assertIsNone(membre.matricule)
        self.assertEqual(membre.institution, 'une_autre_institution')
        self.assertEqual(membre.pays, 'autre_pays')
        self.assertEqual(membre.nom, 'autre_nom')
        self.assertEqual(membre.prenom, 'autre_prenom')
        self.assertEqual(membre.titre.name, 'PROFESSEUR')
        self.assertEqual(membre.genre.name, 'FEMININ')
        self.assertEqual(membre.email, 'autre_email')

    def test_should_pas_trouve_si_modifier_membre_inexistant(self):
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(
                ModifierMembreCommand(
                    uuid_jury='uuid-jury',
                    uuid_membre='uuid-membre-inexistant',
                    matricule=None,
                    institution='une_autre_institution',
                    autre_institution=None,
                    pays='autre_pays',
                    nom='autre_nom',
                    prenom='autre_prenom',
                    titre='PROFESSEUR',
                    justification_non_docteur=None,
                    genre='FEMININ',
                    email='autre_email',
                    langue='FR',
                )
            )
            self.assertIsInstance(context.exception.exceptions.pop(), MembreNonTrouveDansJuryException)

    def test_should_pas_trouve_si_modifier_membre_jury_inexistant(self):
        with self.assertRaises(JuryNonTrouveException):
            self.message_bus.invoke(
                ModifierMembreCommand(
                    uuid_jury='uuid-jury-inexistant',
                    uuid_membre='uuid-membre',
                    matricule=None,
                    institution='une_autre_institution',
                    autre_institution=None,
                    pays='autre_pays',
                    nom='autre_nom',
                    prenom='autre_prenom',
                    titre='PROFESSEUR',
                    justification_non_docteur=None,
                    genre='FEMININ',
                    email='autre_email',
                    langue='FR',
                )
            )

    def test_should_exception_si_modifier_promoteur(self):
        with self.assertRaises(PromoteurModifieException):
            self.message_bus.invoke(
                ModifierMembreCommand(
                    uuid_jury='uuid-jury',
                    uuid_membre='uuid-promoteur',
                    matricule=None,
                    institution='une_autre_institution',
                    autre_institution=None,
                    pays='autre_pays',
                    nom='autre_nom',
                    prenom='autre_prenom',
                    titre='PROFESSEUR',
                    justification_non_docteur=None,
                    genre='FEMININ',
                    email='autre_email',
                    langue='FR',
                )
            )
