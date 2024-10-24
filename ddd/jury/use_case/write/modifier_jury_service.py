##############################################################################
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
##############################################################################
from admission.ddd.admission.doctorat.preparation.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoralIdentity
from parcours_doctoral.ddd.jury.builder.jury_builder import JuryBuilder
from parcours_doctoral.ddd.jury.commands import ModifierJuryCommand
from parcours_doctoral.ddd.jury.domain.model.jury import JuryIdentity
from parcours_doctoral.ddd.jury.repository.i_jury import IJuryRepository
from parcours_doctoral.ddd.repository.i_doctorat import IParcoursDoctoralRepository


def modifier_jury(
    cmd: 'ModifierJuryCommand',
    jury_repository: 'IJuryRepository',
    groupe_de_supervision_repository: 'IGroupeDeSupervisionRepository',
) -> 'JuryIdentity':
    # GIVEN
    groupe_de_supervision = groupe_de_supervision_repository.get_by_doctorat_id(
        ParcoursDoctoralIdentity(uuid=cmd.uuid_doctorat)
    )
    cotutelle = groupe_de_supervision.cotutelle
    jury = JuryBuilder.build(cmd, cotutelle)

    # WHEN
    jury.validate()

    # THEN
    jury_repository.save(jury)
    return jury.entity_id
