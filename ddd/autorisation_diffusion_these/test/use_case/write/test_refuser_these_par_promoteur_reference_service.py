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

import freezegun
from django.test import SimpleTestCase

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from parcours_doctoral.ddd.autorisation_diffusion_these.commands import (
    RefuserTheseParPromoteurReferenceCommand,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.autorisation_diffusion_these import (
    AutorisationDiffusionThese,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.enums import (
    ChoixEtatSignature,
    ChoixStatutAutorisationDiffusionThese,
    RoleActeur,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.validator.exceptions import (
    AutorisationDiffusionTheseNonSoumiseException,
    AutorisationDiffusionTheseNonTrouveException,
    MotifRefusNonSpecifieException,
    SignataireNonInviteException,
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


class TestRefuserTheseParPromoteurReference(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cmd = RefuserTheseParPromoteurReferenceCommand
        cls.message_bus = message_bus_in_memory_instance
        cls.parcours_doctoral_repository = ParcoursDoctoralInMemoryRepository()
        cls.authorisation_diffusion_these_repository = AutorisationDiffusionTheseInMemoryRepository()

    def setUp(self):
        self.addCleanup(self.parcours_doctoral_repository.reset)
        self.addCleanup(self.authorisation_diffusion_these_repository.reset)
        self.parcours_doctoral = ParcoursDoctoralInMemoryRepository.entities[0]
        self.promoteur = SignataireAutorisationDiffusionTheseFactory(
            entity_id__role=RoleActeur.PROMOTEUR,
            entity_id__matricule='234567',
            signature__etat=ChoixEtatSignature.INVITED,
        )
        self.autorisation_diffusion_these: AutorisationDiffusionThese = AutorisationDiffusionTheseFactory(
            statut=ChoixStatutAutorisationDiffusionThese.DIFFUSION_SOUMISE,
            signataires={RoleActeur.PROMOTEUR: self.promoteur},
        )
        self.authorisation_diffusion_these_repository.save(self.autorisation_diffusion_these)
        self.parametres_cmd = {
            'uuid_parcours_doctoral': str(self.autorisation_diffusion_these.entity_id.uuid),
            'matricule_promoteur': '234567',
            'motif_refus': 'Motif',
            'commentaire_interne': 'Commentaire interne',
            'commentaire_externe': 'Commentaire externe',
        }

    def test_doit_generer_exception_si_autorisation_introuvable(self):
        self.parametres_cmd['uuid_parcours_doctoral'] = str(uuid.uuid4())
        with self.assertRaises(AutorisationDiffusionTheseNonTrouveException):
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))

    def test_doit_generer_exception_si_statut_incorrect(self):
        self.autorisation_diffusion_these.statut = ChoixStatutAutorisationDiffusionThese.DIFFUSION_NON_SOUMISE
        self.authorisation_diffusion_these_repository.save(self.autorisation_diffusion_these)
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))
        self.assertIsInstance(e.exception.exceptions.pop(), AutorisationDiffusionTheseNonSoumiseException)

    def test_doit_generer_exception_si_acteur_non_invite(self):
        self.autorisation_diffusion_these.signataires = {
            RoleActeur.PROMOTEUR: SignataireAutorisationDiffusionTheseFactory(
                entity_id__role=RoleActeur.PROMOTEUR,
                entity_id__matricule='234567',
                signature__etat=ChoixEtatSignature.NOT_INVITED,
            )
        }
        self.authorisation_diffusion_these_repository.save(self.autorisation_diffusion_these)
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))
        self.assertIsInstance(e.exception.exceptions.pop(), SignataireNonInviteException)

    def test_doit_generer_exception_si_motif_refus_non_specifie(self):
        self.parametres_cmd['motif_refus'] = ''
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))
        self.assertIsInstance(e.exception.exceptions.pop(), MotifRefusNonSpecifieException)

    @freezegun.freeze_time('2025-01-01')
    def test_doit_modifier_statut_et_enregistrer_informations_refus(self):
        resultat = self.message_bus.invoke(self.cmd(**self.parametres_cmd))

        autorisation = self.authorisation_diffusion_these_repository.get(self.autorisation_diffusion_these.entity_id)

        self.assertEqual(resultat, self.autorisation_diffusion_these.entity_id)

        self.assertEqual(autorisation.statut, ChoixStatutAutorisationDiffusionThese.DIFFUSION_REFUSEE_PROMOTEUR)

        self.assertIsNotNone(autorisation.signataires.get(RoleActeur.PROMOTEUR))
        self.assertIsNone(autorisation.signataires.get(RoleActeur.SCEB))
        self.assertIsNone(autorisation.signataires.get(RoleActeur.ADRE))

        promoteur = autorisation.signataires.get(RoleActeur.PROMOTEUR)
        self.assertEqual(promoteur.entity_id.matricule, '234567')
        self.assertEqual(promoteur.entity_id.role, RoleActeur.PROMOTEUR)
        self.assertEqual(promoteur.signature.commentaire_interne, self.parametres_cmd['commentaire_interne'])
        self.assertEqual(promoteur.signature.etat, ChoixEtatSignature.DECLINED)
        self.assertEqual(promoteur.signature.commentaire_externe, self.parametres_cmd['commentaire_externe'])
        self.assertEqual(promoteur.signature.motif_refus, self.parametres_cmd['motif_refus'])
