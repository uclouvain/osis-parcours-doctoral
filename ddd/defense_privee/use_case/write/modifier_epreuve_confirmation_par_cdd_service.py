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
from parcours_doctoral.ddd.defense_privee.builder.defense_privee_identity import (
    DefensePriveeIdentityBuilder,
)
from parcours_doctoral.ddd.defense_privee.commands import (
    ModifierDefensePriveeParCDDCommand,
)
from parcours_doctoral.ddd.defense_privee.domain.model.defense_privee import (
    DefensePriveeIdentity,
)
from parcours_doctoral.ddd.defense_privee.repository.i_defense_privee import (
    IDefensePriveeRepository,
)


def modifier_defense_privee_par_cdd(
    cmd: 'ModifierDefensePriveeParCDDCommand',
    defense_privee_repository: 'IDefensePriveeRepository',
) -> DefensePriveeIdentity:
    # GIVEN
    defense_privee_id = DefensePriveeIdentityBuilder.build_from_uuid(cmd.uuid)
    defense_privee = defense_privee_repository.get(defense_privee_id)

    # WHEN
    defense_privee.completer(
        date=cmd.date,
        date_limite=cmd.date_limite,
        rapport_recherche=cmd.rapport_recherche,
        proces_verbal_ca=cmd.proces_verbal_ca,
        avis_renouvellement_mandat_recherche=cmd.avis_renouvellement_mandat_recherche,
    )

    # THEN
    return defense_privee_repository.save(defense_privee)
