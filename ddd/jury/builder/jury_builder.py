##############################################################################
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
##############################################################################
from osis_common.ddd import interface

from parcours_doctoral.ddd.jury.builder.jury_identity_builder import JuryIdentityBuilder
from parcours_doctoral.ddd.jury.commands import ModifierJuryCommand
from parcours_doctoral.ddd.jury.domain.model.jury import Jury


class JuryBuilder(interface.RootEntityBuilder):
    @classmethod
    def build_from_repository_dto(cls, dto_object: 'interface.DTO') -> 'Jury':
        raise NotImplementedError

    @classmethod
    def build_from_command(cls, cmd: 'ModifierJuryCommand'):  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    def build(
        cls,
        cmd: 'ModifierJuryCommand',
    ) -> 'Jury':
        entity_id = JuryIdentityBuilder.build_from_uuid(cmd.uuid_parcours_doctoral)
        return Jury(
            entity_id=entity_id,
            titre_propose=cmd.titre_propose,
            formule_defense=cmd.formule_defense,
            date_indicative=cmd.date_indicative,
            langue_redaction=cmd.langue_redaction,
            langue_soutenance=cmd.langue_soutenance,
            commentaire=cmd.commentaire,
        )
