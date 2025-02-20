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
from parcours_doctoral.ddd.read_view.queries import (
    ListerTousParcoursDoctorauxQuery,
    RecupererInformationsTableauBordQuery,
)
from parcours_doctoral.ddd.read_view.use_case import recuperer_informations_tableau_bord, lister_parcours_doctoraux
from parcours_doctoral.infrastructure.parcours_doctoral.read_view.repository.in_memory.liste_parcours_doctoraux import (
    ListeParcoursDoctorauxInMemoryRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.read_view.repository.in_memory.tableau_bord import (
    TableauBordInMemoryRepository,
)


_lister_tous_parcours_doctoraux_in_memory_repository = ListeParcoursDoctorauxInMemoryRepository()


COMMAND_HANDLERS = {
    ListerTousParcoursDoctorauxQuery: lambda msg_bus, cmd: lister_parcours_doctoraux(
        cmd,
        lister_tous_parcours_doctoraux_service=_lister_tous_parcours_doctoraux_in_memory_repository,
    ),
    RecupererInformationsTableauBordQuery: lambda msg_bus, cmd: recuperer_informations_tableau_bord(
        cmd,
        tableau_bord_repository=TableauBordInMemoryRepository(),
    ),
}
