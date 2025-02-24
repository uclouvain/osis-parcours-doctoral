# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from deliberation.models.enums.numero_session import Session
from parcours_doctoral.ddd.formation.builder.activite_identity_builder import (
    ActiviteIdentityBuilder,
)
from parcours_doctoral.ddd.formation.builder.inscription_evaluation_builder import (
    InscriptionEvaluationBuilder,
    InscriptionEvaluationIdentityBuilder,
)
from parcours_doctoral.ddd.formation.commands import (
    InscrireEvaluationCommand,
    ModifierInscriptionEvaluationCommand,
)
from parcours_doctoral.ddd.formation.repository.i_inscription_evaluation import (
    IInscriptionEvaluationRepository,
)


def modifier_inscription_evaluation(
    cmd: ModifierInscriptionEvaluationCommand,
    inscription_evaluation_repository: IInscriptionEvaluationRepository,
):
    # GIVEN
    entity_id = InscriptionEvaluationIdentityBuilder.build_from_uuid(uuid=cmd.inscription_uuid)

    evaluation = inscription_evaluation_repository.get(entity_id=entity_id)

    # WHEN
    evaluation.modifier(
        session=Session[cmd.session],
        inscription_tardive=cmd.inscription_tardive,
    )

    # THEN
    inscription_evaluation_repository.save(evaluation)

    return evaluation.entity_id
