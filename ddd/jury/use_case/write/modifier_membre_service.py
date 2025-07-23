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

from parcours_doctoral.ddd.jury.builder.jury_identity_builder import JuryIdentityBuilder
from parcours_doctoral.ddd.jury.builder.membre_jury_builder import MembreJuryBuilder
from parcours_doctoral.ddd.jury.commands import ModifierMembreCommand
from parcours_doctoral.ddd.jury.domain.model.jury import JuryIdentity
from parcours_doctoral.ddd.jury.repository.i_jury import IJuryRepository


def modifier_membre(
    cmd: 'ModifierMembreCommand',
    jury_repository: 'IJuryRepository',
) -> 'JuryIdentity':
    # GIVEN
    membre = membre = MembreJuryBuilder.build_from_modifier_membre_command(cmd)
    jury = jury_repository.get(JuryIdentityBuilder.build_from_uuid(cmd.uuid_jury))

    # WHEN

    # THEN
    jury.modifier_membre(membre)
    jury_repository.save(jury)
    return jury.entity_id
