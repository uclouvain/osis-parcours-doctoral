# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
import uuid

from parcours_doctoral.ddd.jury.domain.model.jury import JuryIdentity
from osis_common.ddd.interface import CommandRequest, DTO, EntityIdentityBuilder


class JuryIdentityBuilder(EntityIdentityBuilder):
    @classmethod
    def build_from_command(cls, cmd: 'CommandRequest') -> 'JuryIdentity':
        raise NotImplementedError

    @classmethod
    def build_from_repository_dto(cls, dto_object: 'DTO') -> 'JuryIdentity':
        raise NotImplementedError

    @classmethod
    def build_from_uuid(cls, uuid: str) -> 'JuryIdentity':
        return JuryIdentity(uuid=uuid)
