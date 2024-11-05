##############################################################################
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
##############################################################################
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.groupe_de_supervision import \
    GroupeDeSupervisionInMemoryRepository
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import \
    PropositionInMemoryRepository
from parcours_doctoral.ddd.commands import *
from parcours_doctoral.ddd.use_case.read import *
from parcours_doctoral.ddd.use_case.write import *
from parcours_doctoral.ddd.use_case.write.initialiser_parcours_doctoral import initialiser_parcours_doctoral
from parcours_doctoral.infrastructure.parcours_doctoral.domain.service.in_memory.historique import HistoriqueInMemory
from parcours_doctoral.infrastructure.parcours_doctoral.domain.service.in_memory.notification import NotificationInMemory
from parcours_doctoral.infrastructure.parcours_doctoral.epreuve_confirmation.repository.in_memory.epreuve_confirmation import \
    EpreuveConfirmationInMemoryRepository
from parcours_doctoral.infrastructure.parcours_doctoral.repository.in_memory.parcours_doctoral import ParcoursDoctoralInMemoryRepository

_parcours_doctoral_repository = ParcoursDoctoralInMemoryRepository()
_epreuve_confirmation_repository = EpreuveConfirmationInMemoryRepository()
_proposition_repository = PropositionInMemoryRepository()
_groupe_de_supervision_repository = GroupeDeSupervisionInMemoryRepository()
_notification = NotificationInMemory()
_historique = HistoriqueInMemory()


COMMAND_HANDLERS = {
    RecupererParcoursDoctoralQuery: lambda msg_bus, cmd: recuperer_parcours_doctoral(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
    ),
    EnvoyerMessageDoctorantCommand: lambda msg_bus, cmd: envoyer_message_au_doctorant(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        notification=_notification,
        historique=_historique,
    ),
    InitialiserParcoursDoctoralCommand: lambda msg_bus, cmd: initialiser_parcours_doctoral(
        cmd,
        proposition_repository=_proposition_repository,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        groupe_de_supervision_repository=_groupe_de_supervision_repository,
        epreuve_confirmation_repository=_epreuve_confirmation_repository,
        historique=_historique,
    ),
}
