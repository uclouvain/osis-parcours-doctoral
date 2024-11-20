# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from parcours_doctoral.ddd.builder.parcours_doctoral_identity import ParcoursDoctoralIdentityBuilder
from parcours_doctoral.ddd.commands import GetCotutelleQuery
from parcours_doctoral.ddd.dtos import CotutelleDTO
from parcours_doctoral.ddd.repository.i_parcours_doctoral import IParcoursDoctoralRepository


def get_cotutelle(
    cmd: 'GetCotutelleQuery',
    parcours_doctoral_repository: 'IParcoursDoctoralRepository',
) -> 'CotutelleDTO':
    # GIVEN
    parcours_doctoral_id = ParcoursDoctoralIdentityBuilder.build_from_uuid(cmd.uuid_parcours_doctoral)
    # THEN
    return parcours_doctoral_repository.get_cotutelle_dto(parcours_doctoral_id)