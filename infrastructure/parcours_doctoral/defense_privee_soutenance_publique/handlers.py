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
from infrastructure.shared_kernel.personne_connue_ucl.personne_connue_ucl import (
    PersonneConnueUclTranslator,
)
from parcours_doctoral.ddd.defense_privee_soutenance_publique.commands import *
from parcours_doctoral.ddd.defense_privee_soutenance_publique.use_case.write import *
from parcours_doctoral.infrastructure.parcours_doctoral.defense_privee.repository.defense_privee import (
    DefensePriveeRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.defense_privee_soutenance_publique.domain.service.historique import (  # noqa: E501
    Historique,
)
from parcours_doctoral.infrastructure.parcours_doctoral.defense_privee_soutenance_publique.domain.service.notification import (  # noqa: E501
    Notification,
)
from parcours_doctoral.infrastructure.parcours_doctoral.domain.service.notification import (
    Notification as NotificationGenerale,
)
from parcours_doctoral.infrastructure.parcours_doctoral.repository.parcours_doctoral import (
    ParcoursDoctoralRepository,
)

COMMAND_HANDLERS = {
    SoumettreDefensePriveeEtSoutenancePubliqueCommand: lambda msg_bus, cmd: (
        soumettre_defense_privee_et_soutenance_publique(
            cmd,
            parcours_doctoral_repository=ParcoursDoctoralRepository(),
            defense_privee_repository=DefensePriveeRepository(),
            historique=Historique(),
        )
    ),
    AutoriserDefensePriveeEtSoutenancePubliqueCommand: lambda msg_bus, cmd: (
        autoriser_defense_privee_et_soutenance_publique(
            cmd,
            parcours_doctoral_repository=ParcoursDoctoralRepository(),
            historique=Historique(),
            notification=NotificationGenerale(),
        )
    ),
    InviterJuryDefensePriveeEtSoutenancePubliqueCommand: lambda msg_bus, cmd: (
        inviter_jury_defense_privee_et_soutenance_publique(
            cmd,
            parcours_doctoral_repository=ParcoursDoctoralRepository(),
            notification=Notification(),
            personne_connue_ucl_translator=PersonneConnueUclTranslator(),
        )
    ),
    ConfirmerReussiteDefensePriveeEtSoutenancePubliqueCommand: lambda msg_bus, cmd: (
        confirmer_reussite_defense_privee_et_soutenance_publique(
            cmd,
            parcours_doctoral_repository=ParcoursDoctoralRepository(),
            defense_privee_repository=DefensePriveeRepository(),
            historique=Historique(),
            notification=NotificationGenerale(),
        )
    ),
    SoumettreProcesVerbauxDefensePriveeEtSoutenancePubliqueCommand: lambda msg_bus, cmd: (
        soumettre_proces_verbaux_defense_privee_et_soutenance_publique(
            cmd,
            parcours_doctoral_repository=ParcoursDoctoralRepository(),
            defense_privee_repository=DefensePriveeRepository(),
        )
    ),
    ModifierDefensePriveeEtSoutenancePubliqueCommand: lambda msg_bus, cmd: (
        modifier_defense_privee_et_soutenance_publique(
            cmd,
            parcours_doctoral_repository=ParcoursDoctoralRepository(),
            defense_privee_repository=DefensePriveeRepository(),
        )
    ),
}
