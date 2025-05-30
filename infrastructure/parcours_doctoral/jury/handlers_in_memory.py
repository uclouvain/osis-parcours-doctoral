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

from parcours_doctoral.ddd.jury.commands import (
    AjouterMembreCommand,
    ModifierJuryCommand,
    ModifierMembreCommand,
    ModifierRoleMembreCommand,
    RecupererJuryMembreQuery,
    RecupererJuryQuery,
    RetirerMembreCommand,
)
from parcours_doctoral.ddd.jury.use_case.read.recuperer_jury_membre_service import (
    recuperer_jury_membre,
)
from parcours_doctoral.ddd.jury.use_case.read.recuperer_jury_service import (
    recuperer_jury,
)
from parcours_doctoral.ddd.jury.use_case.write.ajouter_membre_service import (
    ajouter_membre,
)
from parcours_doctoral.ddd.jury.use_case.write.modifier_jury_service import (
    modifier_jury,
)
from parcours_doctoral.ddd.jury.use_case.write.modifier_membre_service import (
    modifier_membre,
)
from parcours_doctoral.ddd.jury.use_case.write.modifier_role_membre import (
    modifier_role_membre,
)
from parcours_doctoral.ddd.jury.use_case.write.retirer_membre_service import (
    retirer_membre,
)
from parcours_doctoral.infrastructure.parcours_doctoral.jury.repository.in_memory.jury import (
    JuryInMemoryRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)

_jury_repository = JuryInMemoryRepository()
_groupe_de_supervisition_repository = GroupeDeSupervisionInMemoryRepository()


COMMAND_HANDLERS = {
    RecupererJuryQuery: lambda msg_bus, cmd: recuperer_jury(
        cmd,
        jury_repository=_jury_repository,
    ),
    RecupererJuryMembreQuery: lambda msg_bus, cmd: recuperer_jury_membre(
        cmd,
        jury_repository=_jury_repository,
    ),
    ModifierJuryCommand: lambda msg_bus, cmd: modifier_jury(
        cmd,
        jury_repository=_jury_repository,
    ),
    AjouterMembreCommand: lambda msg_bus, cmd: ajouter_membre(
        cmd,
        jury_repository=_jury_repository,
    ),
    ModifierMembreCommand: lambda msg_bus, cmd: modifier_membre(
        cmd,
        jury_repository=_jury_repository,
    ),
    RetirerMembreCommand: lambda msg_bus, cmd: retirer_membre(
        cmd,
        jury_repository=_jury_repository,
    ),
    ModifierRoleMembreCommand: lambda msg_bus, cmd: modifier_role_membre(
        cmd,
        jury_repository=_jury_repository,
    ),
}
