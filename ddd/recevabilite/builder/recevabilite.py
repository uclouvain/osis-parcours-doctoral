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
import uuid

from osis_common.ddd.interface import CommandRequest, RootEntityBuilder
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.recevabilite.builder.recevabilite_identity import (
    RecevabiliteIdentityBuilder,
)
from parcours_doctoral.ddd.recevabilite.domain.model.recevabilite import Recevabilite
from parcours_doctoral.ddd.recevabilite.dtos import RecevabiliteDTO


class RecevabiliteBuilder(RootEntityBuilder):
    @classmethod
    def build_from_command(cls, cmd: 'CommandRequest') -> 'Recevabilite':
        raise NotImplementedError

    @classmethod
    def build_from_repository_dto(cls, dto_object: 'RecevabiliteDTO') -> 'Recevabilite':
        return Recevabilite(
            entity_id=RecevabiliteIdentityBuilder.build_from_uuid(uuid=dto_object.uuid),
            parcours_doctoral_id=ParcoursDoctoralIdentity(uuid=dto_object.parcours_doctoral_uuid),
            est_active=dto_object.est_active,
            date_decision=dto_object.date_decision,
            date_envoi_manuscrit=dto_object.date_envoi_manuscrit,
            avis_jury=dto_object.avis_jury,
            proces_verbal=dto_object.proces_verbal,
            canevas_proces_verbal=dto_object.canevas_proces_verbal,
        )

    @classmethod
    def build_from_parcours_doctoral_id(cls, parcours_doctoral_id: 'ParcoursDoctoralIdentity') -> 'Recevabilite':
        entity_id = RecevabiliteIdentityBuilder.build_from_uuid(uuid=str(uuid.uuid4()))
        return Recevabilite(
            entity_id=entity_id,
            parcours_doctoral_id=parcours_doctoral_id,
        )
