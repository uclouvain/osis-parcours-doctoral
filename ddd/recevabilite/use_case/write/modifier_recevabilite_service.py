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
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.recevabilite.commands import ModifierRecevabiliteCommand
from parcours_doctoral.ddd.recevabilite.repository.i_recevabilite import (
    IRecevabiliteRepository,
)
from parcours_doctoral.ddd.repository.i_parcours_doctoral import (
    IParcoursDoctoralRepository,
)


def modifier_recevabilite(
    cmd: 'ModifierRecevabiliteCommand',
    parcours_doctoral_repository: 'IParcoursDoctoralRepository',
    recevabilite_repository: 'IRecevabiliteRepository',
) -> ParcoursDoctoralIdentity:
    # GIVEN
    parcours_doctoral_identity = ParcoursDoctoralIdentity(uuid=cmd.parcours_doctoral_uuid)
    recevabilite = recevabilite_repository.get_active(parcours_doctoral_entity_id=parcours_doctoral_identity)
    parcours_doctoral = parcours_doctoral_repository.get(recevabilite.parcours_doctoral_id)

    recevabilite.modifier(
        date_envoi_manuscrit=cmd.date_envoi_manuscrit,
        date_decision=cmd.date_decision,
        proces_verbal=cmd.proces_verbal,
        avis_jury=cmd.avis_jury,
    )

    # WHEN
    parcours_doctoral.modifier_titre_these(titre_these=cmd.titre_these)

    # THEN
    parcours_doctoral_repository.save(parcours_doctoral)
    recevabilite_repository.save(recevabilite)

    return parcours_doctoral_identity
