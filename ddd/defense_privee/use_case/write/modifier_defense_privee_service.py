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
from parcours_doctoral.ddd.defense_privee.builder.defense_privee_identity import (
    DefensePriveeIdentityBuilder,
)
from parcours_doctoral.ddd.defense_privee.commands import ModifierDefensePriveeCommand
from parcours_doctoral.ddd.defense_privee.repository.i_defense_privee import (
    IDefensePriveeRepository,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.domain.service.i_historique import IHistorique
from parcours_doctoral.ddd.repository.i_parcours_doctoral import (
    IParcoursDoctoralRepository,
)


def modifier_defense_privee(
    cmd: 'ModifierDefensePriveeCommand',
    parcours_doctoral_repository: 'IParcoursDoctoralRepository',
    defense_privee_repository: 'IDefensePriveeRepository',
    historique: 'IHistorique',
) -> ParcoursDoctoralIdentity:
    # GIVEN
    defense_privee_id = DefensePriveeIdentityBuilder.build_from_uuid(cmd.uuid)
    defense_privee = defense_privee_repository.get(defense_privee_id)

    parcours_doctoral = parcours_doctoral_repository.get(defense_privee.parcours_doctoral_id)

    defense_privee.modifier(
        date_heure=cmd.date_heure,
        lieu=cmd.lieu,
        date_envoi_manuscrit=cmd.date_envoi_manuscrit,
        proces_verbal=cmd.proces_verbal,
    )

    # WHEN
    parcours_doctoral.modifier_titre_these(titre_these=cmd.titre_these)

    # THEN
    parcours_doctoral_repository.save(parcours_doctoral)
    defense_privee_repository.save(defense_privee)
    historique.historiser_modification_defense_privee(
        parcours_doctoral=parcours_doctoral,
        matricule_auteur=cmd.matricule_auteur,
    )

    return defense_privee.parcours_doctoral_id
