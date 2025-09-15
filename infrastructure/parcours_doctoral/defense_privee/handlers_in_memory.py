##############################################################################
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
##############################################################################
from infrastructure.shared_kernel.personne_connue_ucl.in_memory.personne_connue_ucl import (
    PersonneConnueUclInMemoryTranslator,
)
from parcours_doctoral.ddd.defense_privee.commands import *
from parcours_doctoral.ddd.defense_privee.use_case.read import *
from parcours_doctoral.ddd.defense_privee.use_case.write import *
from parcours_doctoral.infrastructure.parcours_doctoral.defense_privee.domain.service.in_memory.notification import (
    NotificationInMemory,
)
from parcours_doctoral.infrastructure.parcours_doctoral.defense_privee.repository.in_memory.defense_privee import (
    DefensePriveeInMemoryRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.domain.service.in_memory.historique import (
    HistoriqueInMemory,
)
from parcours_doctoral.infrastructure.parcours_doctoral.domain.service.in_memory.notification import (
    NotificationInMemory as NotificationGeneraleInMemory,
)
from parcours_doctoral.infrastructure.parcours_doctoral.repository.in_memory.parcours_doctoral import (
    ParcoursDoctoralInMemoryRepository,
)

_defense_privee_repository = DefensePriveeInMemoryRepository()
_parcours_doctoral_repository = ParcoursDoctoralInMemoryRepository()
_notification = NotificationInMemory()
_notification_generale = NotificationGeneraleInMemory()
_historique = HistoriqueInMemory()
_personne_connue_ucl_translator = PersonneConnueUclInMemoryTranslator()


COMMAND_HANDLERS = {
    RecupererDefensePriveeQuery: lambda msg_bus, cmd: recuperer_defense_privee(
        cmd,
        defense_privee_repository=_defense_privee_repository,
    ),
    RecupererDefensesPriveesQuery: lambda msg_bus, cmd: recuperer_defenses_privees(
        cmd,
        defense_privee_repository=_defense_privee_repository,
    ),
    RecupererDerniereDefensePriveeQuery: lambda msg_bus, cmd: recuperer_derniere_defense_privee(
        cmd,
        defense_privee_repository=_defense_privee_repository,
    ),
    SoumettreDefensePriveeCommand: lambda msg_bus, cmd: soumettre_defense_privee(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        defense_privee_repository=_defense_privee_repository,
        historique=_historique,
    ),
    SoumettreProcesVerbalDefensePriveeCommand: lambda msg_bus, cmd: soumettre_proces_verbal_defense_privee(
        cmd,
        defense_privee_repository=_defense_privee_repository,
        historique=_historique,
    ),
    AutoriserDefensePriveeCommand: lambda msg_bus, cmd: autoriser_defense_privee(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        notification=_notification_generale,
        historique=_historique,
    ),
    InviterJuryDefensePriveeCommand: lambda msg_bus, cmd: inviter_jury_defense_privee(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        notification=_notification,
        historique=_historique,
        personne_connue_ucl_translator=_personne_connue_ucl_translator,
    ),
    ConfirmerReussiteDefensePriveeCommand: lambda msg_bus, cmd: confirmer_reussite_defense_privee(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        defense_privee_repository=_defense_privee_repository,
        historique=_historique,
        notification=_notification_generale,
    ),
}
