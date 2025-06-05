# ##############################################################################
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
# ##############################################################################
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.defense_privee.builder.defense_privee_identity import (
    DefensePriveeIdentityBuilder,
)
from parcours_doctoral.ddd.defense_privee.commands import (
    SoumettreReportDeDateCommand,
)
from parcours_doctoral.ddd.defense_privee.domain.service.i_notification import (
    INotification,
)
from parcours_doctoral.ddd.defense_privee.repository.i_defense_privee import (
    IDefensePriveeRepository,
)


def soumettre_report_de_date(
    cmd: 'SoumettreReportDeDateCommand',
    defense_privee_repository: 'IDefensePriveeRepository',
    notification: 'INotification',
) -> ParcoursDoctoralIdentity:
    # GIVEN
    defense_privee_id = DefensePriveeIdentityBuilder.build_from_uuid(cmd.uuid)
    defense_privee = defense_privee_repository.get(defense_privee_id)

    defense_privee.verifier_demande_prolongation(
        nouvelle_echeance=cmd.nouvelle_echeance,
        justification_succincte=cmd.justification_succincte,
    )

    # WHEN
    defense_privee.faire_demande_prolongation(
        nouvelle_echeance=cmd.nouvelle_echeance,
        justification_succincte=cmd.justification_succincte,
        lettre_justification=cmd.lettre_justification,
    )

    # THEN
    defense_privee_repository.save(defense_privee)
    notification.notifier_nouvelle_echeance(defense_privee=defense_privee)

    return defense_privee.parcours_doctoral_id
