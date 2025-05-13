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
from parcours_doctoral.ddd.formation.builder.evaluation_builder import (
    EvaluationIdentityBuilder,
)
from parcours_doctoral.ddd.formation.builder.inscription_evaluation_builder import (
    InscriptionEvaluationBuilder,
)
from parcours_doctoral.ddd.formation.commands import DesinscrireEvaluationCommand
from parcours_doctoral.ddd.formation.repository.i_evaluation import (
    IEvaluationRepository,
)
from parcours_doctoral.ddd.formation.repository.i_inscription_evaluation import (
    IInscriptionEvaluationRepository,
)


def desinscrire_evaluation(
    cmd: DesinscrireEvaluationCommand,
    inscription_evaluation_repository: IInscriptionEvaluationRepository,
    evaluation_repository: IEvaluationRepository,
):
    # GIVEN
    evaluation_entity_id = EvaluationIdentityBuilder.build_from_uuid(uuid=cmd.inscription_uuid)
    evaluation_dto = evaluation_repository.get_dto(entity_id=evaluation_entity_id)
    inscription_evaluation = InscriptionEvaluationBuilder.build_from_evaluation_dto(evaluation_dto)

    # WHEN
    inscription_evaluation.desinscrire(evaluation_dto.echeance_enseignant)

    # THEN
    inscription_evaluation_repository.save(inscription_evaluation)

    return inscription_evaluation.entity_id
