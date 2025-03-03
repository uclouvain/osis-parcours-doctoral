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
from unittest import TestCase

from deliberation.models.enums.numero_session import Session
from parcours_doctoral.ddd.formation.commands import RecupererInscriptionEvaluationQuery
from parcours_doctoral.ddd.formation.domain.model.activite import ActiviteIdentity
from parcours_doctoral.ddd.formation.domain.model.enums import (
    StatutInscriptionEvaluation,
)
from parcours_doctoral.ddd.formation.domain.model.inscription_evaluation import (
    InscriptionEvaluation,
    InscriptionEvaluationIdentity,
)
from parcours_doctoral.ddd.formation.dtos.evaluation import InscriptionEvaluationDTO
from parcours_doctoral.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from parcours_doctoral.infrastructure.parcours_doctoral.formation.repository.in_memory.inscription_evaluation import (
    InscriptionEvaluationInMemoryRepository,
)


class RecupererInscriptionEvaluationTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.inscription = InscriptionEvaluation(
            entity_id=InscriptionEvaluationIdentity(uuid=str(uuid.uuid4())),
            cours_id=ActiviteIdentity(uuid=str(uuid.uuid4())),
            statut=StatutInscriptionEvaluation.ACCEPTEE,
            session=Session.SEPTEMBER,
            inscription_tardive=True,
        )

        cls.inscription_evaluation_repository = InscriptionEvaluationInMemoryRepository()
        cls.inscription_evaluation_repository.set_entities(entities=[cls.inscription])
        cls.message_bus = message_bus_in_memory_instance

    def test_recuperer_inscription_evaluation(self):
        inscription: InscriptionEvaluationDTO = self.message_bus.invoke(
            command=RecupererInscriptionEvaluationQuery(
                inscription_uuid=self.inscription.entity_id.uuid,
            )
        )

        self.assertEqual(inscription.uuid, self.inscription.entity_id.uuid)
