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
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.domain.validator.exceptions import (
    ParcoursDoctoralNonTrouveException,
)
from parcours_doctoral.ddd.recevabilite.commands import (
    ConfirmerReussiteRecevabiliteCommand,
)
from parcours_doctoral.ddd.recevabilite.test.factory.recevabilite import (
    RecevabiliteFactory,
)
from parcours_doctoral.ddd.recevabilite.validators.exceptions import (
    RecevabiliteNonCompleteePourDecisionReussiteException,
    StatutDoctoratDifferentRecevabiliteSoumiseException,
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


class TestConfirmerReussiteRecevabilite(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cmd = ConfirmerReussiteRecevabiliteCommand
        cls.message_bus = message_bus_in_memory_instance
        cls.recevabilite_repository = RecevabiliteInMemoryRepository()
        cls.parcours_doctoral_repository = ParcoursDoctoralInMemoryRepository()

    def setUp(self):
        self.addCleanup(RecevabiliteInMemoryRepository.reset)
        self.addCleanup(ParcoursDoctoralInMemoryRepository.reset)
        self.parcours_doctoral = self.parcours_doctoral_repository.entities[0]
        self.parcours_doctoral.statut = ChoixStatutParcoursDoctoral.RECEVABILITE_SOUMISE
        self.recevabilite = RecevabiliteFactory(parcours_doctoral_id=self.parcours_doctoral.entity_id)
        self.recevabilite_repository.save(self.recevabilite)
        self.parametres_cmd = {
            'parcours_doctoral_uuid': self.parcours_doctoral.entity_id.uuid,
            'matricule_auteur': '1234',
            'corps_message': 'Corps',
            'sujet_message': 'Sujet',
        }

    def test_should_generer_exception_si_parcours_doctoral_inconnu(self):
        self.parametres_cmd['parcours_doctoral_uuid'] = 'INCONNU'

        with self.assertRaises(ParcoursDoctoralNonTrouveException):
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))

    def test_should_generer_exception_si_statut_parcours_doctoral_invalide(self):
        self.parcours_doctoral.statut = ChoixStatutParcoursDoctoral.ADMIS

        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))

        self.assertIsInstance(e.exception.exceptions.pop(), StatutDoctoratDifferentRecevabiliteSoumiseException)

    def test_should_generer_exception_si_proces_verbal_non_specifie(self):
        self.recevabilite.proces_verbal = []
        self.recevabilite_repository.save(self.recevabilite)

        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))

        self.assertIsInstance(e.exception.exceptions.pop(), RecevabiliteNonCompleteePourDecisionReussiteException)

    def test_should_generer_exception_si_date_non_specifiee(self):
        self.recevabilite.date_decision = None
        self.recevabilite_repository.save(self.recevabilite)

        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))

        self.assertIsInstance(e.exception.exceptions.pop(), RecevabiliteNonCompleteePourDecisionReussiteException)

    def test_should_changer_statut_parcours_doctoral(self):
        resultat = self.message_bus.invoke(self.cmd(**self.parametres_cmd))

        self.assertEqual(resultat, self.parcours_doctoral.entity_id)
        self.assertEqual(self.parcours_doctoral.statut, ChoixStatutParcoursDoctoral.RECEVABILITE_REUSSIE)
