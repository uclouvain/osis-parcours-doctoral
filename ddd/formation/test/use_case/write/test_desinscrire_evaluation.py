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
from unittest import TestCase

import freezegun

from deliberation.models.enums.numero_session import Session
from parcours_doctoral.ddd.formation.builder.evaluation_builder import (
    EvaluationIdentityBuilder,
)
from parcours_doctoral.ddd.formation.builder.inscription_evaluation_builder import (
    InscriptionEvaluationIdentityBuilder,
)
from parcours_doctoral.ddd.formation.commands import DesinscrireEvaluationCommand
from parcours_doctoral.ddd.formation.domain.model.activite import ActiviteIdentity
from parcours_doctoral.ddd.formation.domain.model.enums import (
    StatutInscriptionEvaluation,
)
from parcours_doctoral.ddd.formation.domain.model.evaluation import Evaluation
from parcours_doctoral.ddd.formation.domain.model.inscription_evaluation import (
    InscriptionEvaluation,
)
from parcours_doctoral.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from parcours_doctoral.infrastructure.parcours_doctoral.formation.repository.in_memory.evaluation import (
    EvaluationInMemoryRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.formation.repository.in_memory.inscription_evaluation import (
    InscriptionEvaluationInMemoryRepository,
)


class DesinscrireEvaluationTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evaluation = Evaluation(
            entity_id=EvaluationIdentityBuilder.build(
                annee=2020,
                session=3,
                code_unite_enseignement='UE1',
                noma='123',
            ),
            note_soumise='',
            note_corrigee='',
            cours_id=ActiviteIdentity(uuid=str(uuid.uuid4())),
            uuid=str(uuid.uuid4()),
        )
        cls.inscription = InscriptionEvaluation(
            entity_id=InscriptionEvaluationIdentityBuilder.build_from_uuid(uuid=cls.evaluation.uuid),
            cours_id=ActiviteIdentity(uuid=str(uuid.uuid4())),
            statut=StatutInscriptionEvaluation.ACCEPTEE,
            session=Session.SEPTEMBER,
            inscription_tardive=True,
            desinscription_tardive=False,
        )

        cls.inscription_evaluation_repository = InscriptionEvaluationInMemoryRepository()
        cls.evaluation_repository = EvaluationInMemoryRepository()
        cls.message_bus = message_bus_in_memory_instance
        cls.cmd = DesinscrireEvaluationCommand(
            inscription_uuid=cls.inscription.entity_id.uuid,
        )
        cls.cle_date_defense_privee = cls.evaluation.uuid

    def setUp(self):
        super().setUp()
        self.evaluation_repository.set_entities(entities=[self.evaluation])
        self.evaluation_repository.dates_defenses_privees.pop(self.cle_date_defense_privee, None)
        self.evaluation_repository.periodes_encodage.pop(2020, None)

    def test_desinscrire_evaluation(self):
        identite_inscription_supprimee = self.message_bus.invoke(self.cmd)

        inscription_supprimee = self.inscription_evaluation_repository.get_dto(identite_inscription_supprimee)

        self.assertEqual(inscription_supprimee.uuid, self.inscription.entity_id.uuid)
        self.assertEqual(inscription_supprimee.statut, StatutInscriptionEvaluation.DESINSCRITE.name)
        self.assertEqual(inscription_supprimee.est_acceptee, False)
        self.assertEqual(inscription_supprimee.est_annulee, True)
        self.assertEqual(inscription_supprimee.desinscription_tardive, False)

    def test_desinscrire_evaluation_sans_periode_encodage_ni_date_defense_privee(self):
        identite_inscription_supprimee = self.message_bus.invoke(self.cmd)
        inscription_supprimee = self.inscription_evaluation_repository.get_dto(identite_inscription_supprimee)
        self.assertFalse(inscription_supprimee.desinscription_tardive)

        evaluation_dto = self.evaluation_repository.get_dto(identite_inscription_supprimee)
        self.assertIsNone(evaluation_dto.echeance_enseignant)

    def test_desinscrire_evaluation_sans_periode_encodage_mais_avec_date_defense_privee(self):
        # date limite = date défense privée
        self.evaluation_repository.dates_defenses_privees[self.cle_date_defense_privee] = datetime.date(2021, 1, 15)

        with freezegun.freeze_time('2021-01-13'):
            identite_inscription_supprimee = self.message_bus.invoke(self.cmd)
            inscription_supprimee = self.inscription_evaluation_repository.get_dto(identite_inscription_supprimee)
            self.assertFalse(inscription_supprimee.desinscription_tardive)

            evaluation_dto = self.evaluation_repository.get_dto(identite_inscription_supprimee)
            self.assertEqual(evaluation_dto.echeance_enseignant, datetime.date(2021, 1, 13))

        with freezegun.freeze_time('2021-01-14'):
            identite_inscription_supprimee = self.message_bus.invoke(self.cmd)
            inscription_supprimee = self.inscription_evaluation_repository.get_dto(identite_inscription_supprimee)
            self.assertFalse(inscription_supprimee.desinscription_tardive)

            evaluation_dto = self.evaluation_repository.get_dto(identite_inscription_supprimee)
            self.assertEqual(evaluation_dto.echeance_enseignant, datetime.date(2021, 1, 13))

    def test_desinscrire_evaluation_avec_date_defense_privee_dans_periode_encodage(self):
        # -> date limite = date défense privée
        self.evaluation_repository.dates_defenses_privees[self.cle_date_defense_privee] = datetime.date(2021, 1, 15)
        self.evaluation_repository.periodes_encodage[2020] = {
            3: (
                datetime.date(2021, 1, 1),
                datetime.date(2021, 1, 30),
            )
        }

        with freezegun.freeze_time('2021-01-13'):
            identite_inscription_supprimee = self.message_bus.invoke(self.cmd)
            inscription_supprimee = self.inscription_evaluation_repository.get_dto(identite_inscription_supprimee)
            self.assertTrue(inscription_supprimee.desinscription_tardive)

            evaluation_dto = self.evaluation_repository.get_dto(identite_inscription_supprimee)
            self.assertEqual(evaluation_dto.echeance_enseignant, datetime.date(2021, 1, 13))

        with freezegun.freeze_time('2021-01-14'):
            identite_inscription_supprimee = self.message_bus.invoke(self.cmd)
            inscription_supprimee = self.inscription_evaluation_repository.get_dto(identite_inscription_supprimee)
            self.assertTrue(inscription_supprimee.desinscription_tardive)

            evaluation_dto = self.evaluation_repository.get_dto(identite_inscription_supprimee)
            self.assertEqual(evaluation_dto.echeance_enseignant, datetime.date(2021, 1, 13))

    def test_desinscrire_evaluation_avec_date_defense_privee_hors_periode_encodage(self):
        # -> date limite = fin période d'encodage
        self.evaluation_repository.dates_defenses_privees[self.cle_date_defense_privee] = datetime.date(2021, 12, 31)
        self.evaluation_repository.periodes_encodage[2020] = {
            3: (
                datetime.date(2021, 1, 1),
                datetime.date(2021, 1, 30),
            )
        }

        with freezegun.freeze_time('2021-01-30'):
            identite_inscription_supprimee = self.message_bus.invoke(self.cmd)
            inscription_supprimee = self.inscription_evaluation_repository.get_dto(identite_inscription_supprimee)
            self.assertTrue(inscription_supprimee.desinscription_tardive)

            evaluation_dto = self.evaluation_repository.get_dto(identite_inscription_supprimee)
            self.assertEqual(evaluation_dto.echeance_enseignant, datetime.date(2021, 1, 30))

        with freezegun.freeze_time('2021-02-01'):
            identite_inscription_supprimee = self.message_bus.invoke(self.cmd)
            inscription_supprimee = self.inscription_evaluation_repository.get_dto(identite_inscription_supprimee)
            self.assertTrue(inscription_supprimee.desinscription_tardive)

            evaluation_dto = self.evaluation_repository.get_dto(identite_inscription_supprimee)
            self.assertEqual(evaluation_dto.echeance_enseignant, datetime.date(2021, 1, 30))

    def test_desinscrire_evaluation_avec_periode_encodage_sans_date_defense_privee(self):
        # -> date limite = début période d'encodage
        self.evaluation_repository.periodes_encodage[2020] = {
            3: (datetime.date(2021, 1, 1), datetime.date(2021, 1, 30)),
        }

        with freezegun.freeze_time('2020-12-31'):
            identite_inscription_supprimee = self.message_bus.invoke(self.cmd)
            inscription_supprimee = self.inscription_evaluation_repository.get_dto(identite_inscription_supprimee)
            self.assertFalse(inscription_supprimee.desinscription_tardive)

            evaluation_dto = self.evaluation_repository.get_dto(identite_inscription_supprimee)
            self.assertEqual(evaluation_dto.echeance_enseignant, datetime.date(2021, 1, 30))

        with freezegun.freeze_time('2021-01-01'):
            identite_inscription_supprimee = self.message_bus.invoke(self.cmd)
            inscription_supprimee = self.inscription_evaluation_repository.get_dto(identite_inscription_supprimee)
            self.assertTrue(inscription_supprimee.desinscription_tardive)

            evaluation_dto = self.evaluation_repository.get_dto(identite_inscription_supprimee)
            self.assertEqual(evaluation_dto.echeance_enseignant, datetime.date(2021, 1, 30))
