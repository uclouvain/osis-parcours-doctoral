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
import uuid

from django.test import SimpleTestCase

from parcours_doctoral.ddd.autorisation_diffusion_these.commands import (
    RecupererAutorisationDiffusionTheseQuery,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.autorisation_diffusion_these import (
    AutorisationDiffusionThese,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.enums import (
    RoleActeur,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.validator.exceptions import (
    AutorisationDiffusionTheseNonTrouveException,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.dtos.autorisation_diffusion_these import (
    AutorisationDiffusionTheseDTO,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.test.factory.autorisation_diffusion_these import (
    AutorisationDiffusionTheseFactory,
    SignataireAutorisationDiffusionTheseFactory,
)
from parcours_doctoral.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from parcours_doctoral.infrastructure.parcours_doctoral.autorisation_diffusion_these.repository.in_memory.autorisation_diffusion_these import (  # noqa: E501
    AutorisationDiffusionTheseInMemoryRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.repository.in_memory.parcours_doctoral import (
    ParcoursDoctoralInMemoryRepository,
)


class TestRecupererAutorisationDiffusionThese(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cmd = RecupererAutorisationDiffusionTheseQuery
        cls.message_bus = message_bus_in_memory_instance
        cls.parcours_doctoral_repository = ParcoursDoctoralInMemoryRepository()
        cls.authorisation_diffusion_these_repository = AutorisationDiffusionTheseInMemoryRepository()

    def setUp(self):
        self.addCleanup(self.parcours_doctoral_repository.reset)
        self.addCleanup(self.authorisation_diffusion_these_repository.reset)
        self.parcours_doctoral = ParcoursDoctoralInMemoryRepository.entities[0]
        self.autorisation_diffusion_these: AutorisationDiffusionThese = AutorisationDiffusionTheseFactory(
            signataires={RoleActeur.PROMOTEUR: SignataireAutorisationDiffusionTheseFactory()}
        )
        self.authorisation_diffusion_these_repository.save(self.autorisation_diffusion_these)
        self.parametres_cmd = {
            'uuid_parcours_doctoral': str(self.autorisation_diffusion_these.entity_id.uuid),
        }

    def test_should_generer_exception_si_autorisation_introuvable(self):
        with self.assertRaises(AutorisationDiffusionTheseNonTrouveException):
            self.message_bus.invoke(self.cmd(uuid_parcours_doctoral=str(uuid.uuid4())))

    def test_should_recuperer_informations_autorisation_diffusion_these(self):
        resultat: AutorisationDiffusionTheseDTO = self.message_bus.invoke(self.cmd(**self.parametres_cmd))

        self.assertEqual(resultat.uuid, str(self.autorisation_diffusion_these.entity_id.uuid))
        self.assertEqual(resultat.statut, self.autorisation_diffusion_these.statut.name)
        self.assertEqual(resultat.sources_financement, self.autorisation_diffusion_these.sources_financement)
        self.assertEqual(resultat.resume_anglais, self.autorisation_diffusion_these.resume_anglais)
        self.assertEqual(resultat.resume_autre_langue, self.autorisation_diffusion_these.resume_autre_langue)
        self.assertEqual(resultat.mots_cles, self.autorisation_diffusion_these.mots_cles)
        self.assertEqual(
            resultat.type_modalites_diffusion,
            self.autorisation_diffusion_these.type_modalites_diffusion.name,
        )
        self.assertEqual(resultat.date_embargo, self.autorisation_diffusion_these.date_embargo)
        self.assertEqual(
            resultat.limitations_additionnelles_chapitres,
            self.autorisation_diffusion_these.limitations_additionnelles_chapitres,
        )
        self.assertEqual(
            resultat.modalites_diffusion_acceptees_le,
            self.autorisation_diffusion_these.modalites_diffusion_acceptees_le,
        )

        self.assertEqual(len(resultat.signataires), 1)
        signataire_original = self.autorisation_diffusion_these.signataires[RoleActeur.PROMOTEUR]
        signataire_recupere = resultat.signataires[0]
        self.assertEqual(signataire_recupere.uuid, '')
        self.assertEqual(signataire_recupere.matricule, signataire_original.entity_id.matricule)
        self.assertEqual(signataire_recupere.role, signataire_original.entity_id.role.name)
        self.assertEqual(signataire_recupere.signature.etat, signataire_original.signature.etat.name)
        self.assertEqual(
            signataire_recupere.signature.commentaire_externe,
            signataire_original.signature.commentaire_externe,
        )
        self.assertEqual(
            signataire_recupere.signature.commentaire_interne,
            signataire_original.signature.commentaire_interne,
        )
        self.assertEqual(signataire_recupere.signature.motif_refus, signataire_original.signature.motif_refus)
