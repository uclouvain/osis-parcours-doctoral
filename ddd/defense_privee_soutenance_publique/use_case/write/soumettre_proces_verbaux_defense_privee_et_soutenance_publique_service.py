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
from parcours_doctoral.ddd.builder.parcours_doctoral_identity import (
    ParcoursDoctoralIdentityBuilder,
)
from parcours_doctoral.ddd.defense_privee.repository.i_defense_privee import (
    IDefensePriveeRepository,
)
from parcours_doctoral.ddd.defense_privee_soutenance_publique.commands import (
    SoumettreProcesVerbauxDefensePriveeEtSoutenancePubliqueCommand,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.repository.i_parcours_doctoral import (
    IParcoursDoctoralRepository,
)


def soumettre_proces_verbaux_defense_privee_et_soutenance_publique(
    cmd: 'SoumettreProcesVerbauxDefensePriveeEtSoutenancePubliqueCommand',
    parcours_doctoral_repository: 'IParcoursDoctoralRepository',
    defense_privee_repository: 'IDefensePriveeRepository',
) -> ParcoursDoctoralIdentity:
    # GIVEN
    parcours_doctoral_id = ParcoursDoctoralIdentityBuilder.build_from_uuid(cmd.uuid_parcours_doctoral)
    parcours_doctoral = parcours_doctoral_repository.get(parcours_doctoral_id)

    defense_privee = defense_privee_repository.get_active(parcours_doctoral_entity_id=parcours_doctoral_id)

    # WHEN
    parcours_doctoral.soumettre_proces_verbaux_defense_privee_et_soutenance_publique_formule_2(
        proces_verbal_soutenance_publique=cmd.proces_verbal_soutenance_publique,
    )

    defense_privee.soumettre_proces_verbal(proces_verbal=cmd.proces_verbal_defense_privee)

    # THEN
    parcours_doctoral_repository.save(parcours_doctoral)
    defense_privee_repository.save(defense_privee)

    return parcours_doctoral_id
