# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime

import factory
import freezegun
from dateutil.relativedelta import relativedelta
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.test.factory.proposition import (
    PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
    _PropositionIdentityFactory,
)
from admission.ddd.admission.test.factory.formation import FormationIdentityFactory
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from parcours_doctoral.ddd.commands import InitialiserParcoursDoctoralCommand
from parcours_doctoral.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from parcours_doctoral.infrastructure.parcours_doctoral.epreuve_confirmation.repository.in_memory.epreuve_confirmation import (
    EpreuveConfirmationInMemoryRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.repository.in_memory.parcours_doctoral import (
    ParcoursDoctoralInMemoryRepository,
)


@freezegun.freeze_time('2021-01-01')
class TestInitialiserParcoursDoctoral(TestCase):
    def setUp(self) -> None:
        self.proposition = PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(
            entity_id=factory.SubFactory(_PropositionIdentityFactory, uuid='uuid-SC3DP-APPROVED'),
            matricule_candidat='0123456789',
            formation_id=FormationIdentityFactory(sigle="SC3DP", annee=2020),
            curriculum=['file1.pdf'],
            est_confirmee=True,
            est_approuvee_par_sic=True,
            est_approuvee_par_fac=True,
            approuvee_par_cdd_le=datetime.datetime(2020, 2, 2),
        )

        self.proposition_repository = PropositionInMemoryRepository()
        self.proposition_repository.save(self.proposition)

        self.epreuve_confirmation_repository = EpreuveConfirmationInMemoryRepository()
        self.parcours_doctoral_repository = ParcoursDoctoralInMemoryRepository()
        self.groupe_de_supervision_repository = GroupeDeSupervisionInMemoryRepository()
        self.addCleanup(self.groupe_de_supervision_repository.reset)
        self.addCleanup(self.parcours_doctoral_repository.reset)

        self.message_bus = message_bus_in_memory_instance
        self.cmd = InitialiserParcoursDoctoralCommand(proposition_uuid=self.proposition.entity_id.uuid)

    def test_should_initialiser_parcours_doctoral(self):
        id_parcours_doctoral_cree = self.message_bus.invoke(self.cmd)

        epreuves_confirmations = self.epreuve_confirmation_repository.search_by_parcours_doctoral_identity(
            parcours_doctoral_entity_id=id_parcours_doctoral_cree,
        )

        self.assertEqual(len(epreuves_confirmations), 1)
        self.assertEqual(
            epreuves_confirmations[0].date_limite,
            datetime.datetime(2022, 2, 2),
        )

    def test_should_initialiser_parcours_doctoral_sans_date_acceptation_cdd(self):
        self.proposition.approuvee_par_cdd_le = None

        id_parcours_doctoral_cree = self.message_bus.invoke(self.cmd)

        epreuves_confirmation = self.epreuve_confirmation_repository.search_by_parcours_doctoral_identity(
            parcours_doctoral_entity_id=id_parcours_doctoral_cree,
        )

        self.assertEqual(len(epreuves_confirmation), 1)
        self.assertEqual(
            epreuves_confirmation[0].date_limite,
            datetime.date(2023, 1, 1),
        )
