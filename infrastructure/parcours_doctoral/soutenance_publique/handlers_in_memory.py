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
from parcours_doctoral.ddd.soutenance_publique.commands import *
from parcours_doctoral.ddd.soutenance_publique.use_case.write import *
from parcours_doctoral.infrastructure.parcours_doctoral.domain.service.in_memory.historique import (
    HistoriqueInMemory,
)
from parcours_doctoral.infrastructure.parcours_doctoral.domain.service.in_memory.notification import (
    NotificationInMemory as NotificationGeneraleInMemory,
)
from parcours_doctoral.infrastructure.parcours_doctoral.repository.in_memory.parcours_doctoral import (
    ParcoursDoctoralInMemoryRepository,
)

from .domain.service.in_memory.notification import NotificationInMemory

_parcours_doctoral_repository = ParcoursDoctoralInMemoryRepository()
_notification_generale = NotificationGeneraleInMemory()
_notification = NotificationInMemory()
_historique = HistoriqueInMemory()


COMMAND_HANDLERS = {
    SoumettreSoutenancePubliqueCommand: lambda msg_bus, cmd: soumettre_soutenance_publique(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        historique=_historique,
    ),
    InviterJurySoutenancePubliqueCommand: lambda msg_bus, cmd: inviter_jury_soutenance_publique(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        notification=_notification,
        personne_connue_ucl_translator=PersonneConnueUclInMemoryTranslator(),
    ),
}
