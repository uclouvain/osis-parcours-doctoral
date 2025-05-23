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
from parcours_doctoral.ddd.formation.commands import *
from parcours_doctoral.ddd.formation.use_case.read import *
from parcours_doctoral.ddd.formation.use_case.write import *
from parcours_doctoral.ddd.formation.use_case.write.inscrire_evaluation_service import (
    inscrire_evaluation,
)

from ..repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from ..repository.in_memory.parcours_doctoral import ParcoursDoctoralInMemoryRepository
from .domain.service.in_memory.notification import NotificationInMemory
from .repository.in_memory.activite import ActiviteInMemoryRepository
from .repository.in_memory.inscription_evaluation import (
    InscriptionEvaluationInMemoryRepository,
)

_activite_repository = ActiviteInMemoryRepository()
_parcours_doctoral_repository = ParcoursDoctoralInMemoryRepository()
_groupe_de_supervision_repository = GroupeDeSupervisionInMemoryRepository()
_notification = NotificationInMemory()
_inscription_evaluation_repository = InscriptionEvaluationInMemoryRepository()


COMMAND_HANDLERS = {
    SupprimerActiviteCommand: lambda msg_bus, cmd: supprimer_activite(
        cmd,
        activite_repository=_activite_repository,
    ),
    SoumettreActivitesCommand: lambda msg_bus, cmd: soumettre_activites(
        cmd,
        activite_repository=_activite_repository,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        groupe_de_supervision_repository=_groupe_de_supervision_repository,
        notification=_notification,
    ),
    DonnerAvisSurActiviteCommand: lambda msg_bus, cmd: donner_avis_sur_activite(
        cmd,
        activite_repository=_activite_repository,
    ),
    AccepterActivitesCommand: lambda msg_bus, cmd: accepter_activites(
        cmd,
        activite_repository=_activite_repository,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        notification=_notification,
    ),
    RefuserActiviteCommand: lambda msg_bus, cmd: refuser_activite(
        cmd,
        activite_repository=_activite_repository,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        notification=_notification,
    ),
    RevenirSurStatutActiviteCommand: lambda msg_bus, cmd: revenir_sur_statut_activite(
        cmd,
        activite_repository=_activite_repository,
    ),
    RecupererInscriptionsEvaluationsQuery: lambda msg_bus, cmd: recuperer_inscriptions_evaluations(
        cmd,
        inscription_evaluation_repository=_inscription_evaluation_repository,
    ),
    RecupererInscriptionEvaluationQuery: lambda msg_bus, cmd: recuperer_inscription_evaluation(
        cmd,
        inscription_evaluation_repository=_inscription_evaluation_repository,
    ),
    InscrireEvaluationCommand: lambda msg_bus, cmd: inscrire_evaluation(
        cmd,
        inscription_evaluation_repository=_inscription_evaluation_repository,
    ),
    ModifierInscriptionEvaluationCommand: lambda msg_bus, cmd: modifier_inscription_evaluation(
        cmd,
        inscription_evaluation_repository=_inscription_evaluation_repository,
    ),
    DesinscrireEvaluationCommand: lambda msg_bus, cmd: desinscrire_evaluation(
        cmd,
        inscription_evaluation_repository=_inscription_evaluation_repository,
    ),
}
