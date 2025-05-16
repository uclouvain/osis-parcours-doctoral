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
from infrastructure.encodage_de_notes.shared_kernel.service.periode_encodage_notes import (
    PeriodeEncodageNotesTranslator,
)
from parcours_doctoral.ddd.formation.commands import *
from parcours_doctoral.ddd.formation.use_case.read import *
from parcours_doctoral.ddd.formation.use_case.write import *
from parcours_doctoral.ddd.formation.use_case.write.inscrire_evaluation_service import (
    inscrire_evaluation,
)
from parcours_doctoral.infrastructure.parcours_doctoral.formation.domain.service.inscription_unite_enseignement import (
    InscriptionUniteEnseignementTranslator,
)
from parcours_doctoral.infrastructure.parcours_doctoral.formation.domain.service.notification import (
    Notification,
)
from parcours_doctoral.infrastructure.parcours_doctoral.formation.repository.activite import (
    ActiviteRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.formation.repository.evaluation import (
    EvaluationRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.formation.repository.inscription_evaluation import (
    InscriptionEvaluationRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.repository.groupe_de_supervision import (
    GroupeDeSupervisionRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.repository.parcours_doctoral import (
    ParcoursDoctoralRepository,
)

COMMAND_HANDLERS = {
    SupprimerActiviteCommand: lambda msg_bus, cmd: supprimer_activite(
        cmd,
        activite_repository=ActiviteRepository(),
    ),
    SoumettreActivitesCommand: lambda msg_bus, cmd: soumettre_activites(
        cmd,
        activite_repository=ActiviteRepository(),
        parcours_doctoral_repository=ParcoursDoctoralRepository(),
        groupe_de_supervision_repository=GroupeDeSupervisionRepository(),
        notification=Notification(),
    ),
    DonnerAvisSurActiviteCommand: lambda msg_bus, cmd: donner_avis_sur_activite(
        cmd,
        activite_repository=ActiviteRepository(),
    ),
    AccepterActivitesCommand: lambda msg_bus, cmd: accepter_activites(
        cmd,
        activite_repository=ActiviteRepository(),
        parcours_doctoral_repository=ParcoursDoctoralRepository(),
        notification=Notification(),
    ),
    RefuserActiviteCommand: lambda msg_bus, cmd: refuser_activite(
        cmd,
        activite_repository=ActiviteRepository(),
        parcours_doctoral_repository=ParcoursDoctoralRepository(),
        notification=Notification(),
    ),
    RevenirSurStatutActiviteCommand: lambda msg_bus, cmd: revenir_sur_statut_activite(
        cmd,
        activite_repository=ActiviteRepository(),
    ),
    RecupererInscriptionsEvaluationsQuery: lambda msg_bus, cmd: recuperer_inscriptions_evaluations(
        cmd,
        inscription_evaluation_repository=InscriptionEvaluationRepository(),
    ),
    RecupererInscriptionEvaluationQuery: lambda msg_bus, cmd: recuperer_inscription_evaluation(
        cmd,
        inscription_evaluation_repository=InscriptionEvaluationRepository(),
    ),
    InscrireEvaluationCommand: lambda msg_bus, cmd: inscrire_evaluation(
        cmd,
        inscription_evaluation_repository=InscriptionEvaluationRepository(),
    ),
    ModifierInscriptionEvaluationCommand: lambda msg_bus, cmd: modifier_inscription_evaluation(
        cmd,
        inscription_evaluation_repository=InscriptionEvaluationRepository(),
    ),
    DesinscrireEvaluationCommand: lambda msg_bus, cmd: desinscrire_evaluation(
        cmd,
        evaluation_repository=EvaluationRepository(),
        inscription_evaluation_repository=InscriptionEvaluationRepository(),
    ),
    ListerEvaluationsQuery: lambda msg_bus, cmd: lister_evaluations(
        cmd,
        evaluation_repository=EvaluationRepository(),
    ),
    EncoderNoteCommand: lambda msg_bus, cmd: encoder_note(
        cmd,
        evaluation_repository=EvaluationRepository(),
        activite_repository=ActiviteRepository(),
    ),
    ListerInscriptionsUnitesEnseignementQuery: lambda msg_bus, cmd: lister_inscriptions_unites_enseignement(
        cmd,
        inscriptions_unites_enseignement_translator=InscriptionUniteEnseignementTranslator(),
    ),
}
