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
import datetime
import uuid

import freezegun
from django.test import SimpleTestCase

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from parcours_doctoral.ddd.autorisation_diffusion_these.commands import (
    EnvoyerFormulaireAutorisationDiffusionTheseAuPromoteurReferenceCommand,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.autorisation_diffusion_these import (
    AutorisationDiffusionThese,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.enums import (
    ChoixEtatSignature,
    ChoixStatutAutorisationDiffusionThese,
    RoleActeur,
    TypeModalitesDiffusionThese,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.validator.exceptions import (
    AutorisationDiffusionTheseDejaSoumiseException,
    AutorisationDiffusionTheseNonTrouveException,
    DateEmbargoModalitesDiffusionNonCompleteeException,
    LangueRedactionTheseNonCompleteeException,
    ModalitesDiffusionNonAccepteesException,
    MotsClesNonCompletesException,
    ResumeAnglaisNonCompleteException,
    SourcesFinancementsNonCompleteesException,
    TypeModalitesDiffusionNonCompleteException,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.test.factory.autorisation_diffusion_these import (
    AutorisationDiffusionTheseFactory,
    SignataireAutorisationDiffusionTheseFactory,
    SignataireAutorisationDiffusionTheseIdentityFactory,
    SignatureAutorisationDiffusionTheseFactory,
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


class TestEnvoyerFormulaireAutorisationDiffusionTheseAuPromoteurReference(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cmd = EnvoyerFormulaireAutorisationDiffusionTheseAuPromoteurReferenceCommand
        cls.message_bus = message_bus_in_memory_instance
        cls.parcours_doctoral_repository = ParcoursDoctoralInMemoryRepository()
        cls.authorisation_diffusion_these_repository = AutorisationDiffusionTheseInMemoryRepository()

    def setUp(self):
        self.addCleanup(self.parcours_doctoral_repository.reset)
        self.addCleanup(self.authorisation_diffusion_these_repository.reset)
        self.parcours_doctoral = ParcoursDoctoralInMemoryRepository.entities[0]
        self.autorisation_diffusion_these: AutorisationDiffusionThese = AutorisationDiffusionTheseFactory()
        self.authorisation_diffusion_these_repository.save(self.autorisation_diffusion_these)
        self.parametres_cmd = {
            'uuid_parcours_doctoral': str(self.autorisation_diffusion_these.entity_id.uuid),
            'sources_financement': 'Sources modifiees',
            'resume_anglais': 'Resume en anglais modifié',
            'resume_autre_langue': 'Résumé dans une autre langue modifié',
            'langue_redaction_these': 'Langue de rédaction de la thèse modifiée',
            'mots_cles': ['mot-1', 'mot-2'],
            'type_modalites_diffusion': TypeModalitesDiffusionThese.ACCES_RESTREINT.name,
            'date_embargo': datetime.date(2025, 11, 1),
            'limitations_additionnelles_chapitres': 'Limitations modifiées',
            'modalites_diffusion_acceptees': 'Modalités acceptées réactualisées',
        }

    def test_doit_generer_exception_si_autorisation_introuvable(self):
        self.parametres_cmd['uuid_parcours_doctoral'] = str(uuid.uuid4())
        with self.assertRaises(AutorisationDiffusionTheseNonTrouveException):
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))

    def test_doit_generer_exception_si_statut_incorrect(self):
        self.autorisation_diffusion_these.statut = ChoixStatutAutorisationDiffusionThese.DIFFUSION_SOUMISE
        self.authorisation_diffusion_these_repository.save(self.autorisation_diffusion_these)
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))
        self.assertIsInstance(e.exception.exceptions.pop(), AutorisationDiffusionTheseDejaSoumiseException)

    def test_doit_generer_exception_si_sources_financement_non_completees(self):
        self.parametres_cmd['sources_financement'] = ''
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))
        self.assertIsInstance(e.exception.exceptions.pop(), SourcesFinancementsNonCompleteesException)

    def test_doit_generer_exception_si_resume_anglais_non_complete(self):
        self.parametres_cmd['resume_anglais'] = ''
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))
        self.assertIsInstance(e.exception.exceptions.pop(), ResumeAnglaisNonCompleteException)

    def test_doit_generer_exception_si_langue_redaction_these_non_completee(self):
        self.parametres_cmd['langue_redaction_these'] = ''
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))
        self.assertIsInstance(e.exception.exceptions.pop(), LangueRedactionTheseNonCompleteeException)

    def test_doit_generer_exception_si_mots_cles_non_completes(self):
        self.parametres_cmd['mots_cles'] = []
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))
        self.assertIsInstance(e.exception.exceptions.pop(), MotsClesNonCompletesException)

    def test_doit_generer_exception_si_type_modalites_diffusion_non_complete(self):
        self.parametres_cmd['type_modalites_diffusion'] = ''
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))
        self.assertIsInstance(e.exception.exceptions.pop(), TypeModalitesDiffusionNonCompleteException)

    def test_doit_generer_exception_si_date_embargo_non_completee(self):
        self.parametres_cmd['type_modalites_diffusion'] = TypeModalitesDiffusionThese.ACCES_EMBARGO.name
        self.parametres_cmd['date_embargo'] = None
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))
        self.assertIsInstance(e.exception.exceptions.pop(), DateEmbargoModalitesDiffusionNonCompleteeException)

    def test_doit_generer_exception_si_modalites_diffusion_non_acceptees(self):
        self.parametres_cmd['modalites_diffusion_acceptees'] = ''
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(self.cmd(**self.parametres_cmd))
        self.assertIsInstance(e.exception.exceptions.pop(), ModalitesDiffusionNonAccepteesException)

    @freezegun.freeze_time('2025-01-01')
    def test_doit_modifier_valeurs_existantes_changer_statut_et_ajouter_promoteur_aux_signataires(self):
        resultat = self.message_bus.invoke(self.cmd(**self.parametres_cmd))

        autorisation = self.authorisation_diffusion_these_repository.get(
            entity_id=self.autorisation_diffusion_these.entity_id
        )

        self.assertEqual(resultat, self.autorisation_diffusion_these.entity_id)

        self.assertEqual(autorisation.sources_financement, self.parametres_cmd['sources_financement'])
        self.assertEqual(autorisation.resume_anglais, self.parametres_cmd['resume_anglais'])
        self.assertEqual(autorisation.resume_autre_langue, self.parametres_cmd['resume_autre_langue'])
        self.assertEqual(autorisation.langue_redaction_these, self.parametres_cmd['langue_redaction_these'])
        self.assertEqual(autorisation.mots_cles, self.parametres_cmd['mots_cles'])
        self.assertEqual(autorisation.type_modalites_diffusion, TypeModalitesDiffusionThese.ACCES_RESTREINT)
        self.assertEqual(autorisation.date_embargo, self.parametres_cmd['date_embargo'])
        self.assertEqual(
            autorisation.limitations_additionnelles_chapitres,
            self.parametres_cmd['limitations_additionnelles_chapitres'],
        )
        self.assertEqual(
            autorisation.modalites_diffusion_acceptees,
            self.parametres_cmd['modalites_diffusion_acceptees'],
        )
        self.assertEqual(autorisation.modalites_diffusion_acceptees_le, datetime.date(2025, 1, 1))
        self.assertEqual(autorisation.statut, ChoixStatutAutorisationDiffusionThese.DIFFUSION_SOUMISE)

        self.assertIsNotNone(autorisation.signataires.get(RoleActeur.PROMOTEUR))
        self.assertIsNone(autorisation.signataires.get(RoleActeur.SCEB))
        self.assertIsNone(autorisation.signataires.get(RoleActeur.ADRE))

        promoteur = autorisation.signataires.get(RoleActeur.PROMOTEUR)
        self.assertEqual(promoteur.entity_id.matricule, '234567')
        self.assertEqual(promoteur.entity_id.role, RoleActeur.PROMOTEUR)
        self.assertEqual(promoteur.signature.commentaire_interne, '')
        self.assertEqual(promoteur.signature.etat, ChoixEtatSignature.INVITED)
        self.assertEqual(promoteur.signature.commentaire_externe, '')
        self.assertEqual(promoteur.signature.motif_refus, '')

    def test_should_modifier_promoteur_existant(self):
        self.autorisation_diffusion_these.signataires[RoleActeur.PROMOTEUR] = (
            SignataireAutorisationDiffusionTheseFactory(
                entity_id=SignataireAutorisationDiffusionTheseIdentityFactory(
                    role=RoleActeur.PROMOTEUR,
                    matricule='234567',
                ),
                signature=SignatureAutorisationDiffusionTheseFactory(
                    commentaire_interne='Commentaire interne',
                    commentaire_externe='Commentaire externe',
                    motif_refus='Motifs refus',
                ),
            )
        )
        self.authorisation_diffusion_these_repository.save(self.autorisation_diffusion_these)

        resultat = self.message_bus.invoke(self.cmd(**self.parametres_cmd))

        autorisation = self.authorisation_diffusion_these_repository.get(
            entity_id=self.autorisation_diffusion_these.entity_id
        )

        self.assertEqual(resultat, self.autorisation_diffusion_these.entity_id)

        self.assertEqual(autorisation.statut, ChoixStatutAutorisationDiffusionThese.DIFFUSION_SOUMISE)
        self.assertIsNotNone(autorisation.signataires.get(RoleActeur.PROMOTEUR))
        self.assertIsNone(autorisation.signataires.get(RoleActeur.SCEB))
        self.assertIsNone(autorisation.signataires.get(RoleActeur.ADRE))

        promoteur = autorisation.signataires.get(RoleActeur.PROMOTEUR)
        self.assertEqual(promoteur.entity_id.matricule, '234567')
        self.assertEqual(promoteur.entity_id.role, RoleActeur.PROMOTEUR)
        self.assertEqual(promoteur.signature.commentaire_interne, '')
        self.assertEqual(promoteur.signature.etat, ChoixEtatSignature.INVITED)
        self.assertEqual(promoteur.signature.commentaire_externe, '')
        self.assertEqual(promoteur.signature.motif_refus, '')
