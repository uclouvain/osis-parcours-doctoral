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
from parcours_doctoral.ddd.formation.commands import EncoderNoteCommand
from parcours_doctoral.ddd.formation.domain.service.i_notification import INotification
from parcours_doctoral.ddd.formation.repository.i_activite import IActiviteRepository
from parcours_doctoral.ddd.formation.repository.i_evaluation import (
    IEvaluationRepository,
)


def encoder_note(
    cmd: EncoderNoteCommand,
    evaluation_repository: IEvaluationRepository,
    activite_repository: IActiviteRepository,
    notification: INotification,
):
    # GIVEN
    identite_evaluation = EvaluationIdentityBuilder.build(
        annee=cmd.annee,
        session=cmd.session,
        code_unite_enseignement=cmd.code_unite_enseignement,
        noma=cmd.noma,
    )
    evaluation = evaluation_repository.get(entity_id=identite_evaluation)
    cours = activite_repository.get(entity_id=evaluation.cours_id)

    # WHEN
    evaluation.encoder_note(note=cmd.note)
    cours.encoder_note_cours_ucl(note=cmd.note)

    # THEN
    evaluation_repository.save(evaluation)
    activite_repository.save(cours)
    notification.notifier_encodage_note_aux_gestionnaires(evaluation=evaluation, cours=cours)

    return evaluation.entity_id
