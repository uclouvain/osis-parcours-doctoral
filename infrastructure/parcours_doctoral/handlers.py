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
from admission.ddd.admission.doctorat.events import InscriptionDoctoraleApprouveeParSicEvent, \
    AdmissionDoctoraleApprouveeParSicEvent
from admission.infrastructure.admission.doctorat.preparation.repository.groupe_de_supervision import \
    GroupeDeSupervisionRepository
from admission.infrastructure.admission.doctorat.preparation.repository.proposition import PropositionRepository
from parcours_doctoral.ddd.commands import *
from parcours_doctoral.ddd.use_case.read import *
from parcours_doctoral.ddd.use_case.write import *
from .domain.service.historique import Historique
from .domain.service.notification import Notification
from .epreuve_confirmation.repository.epreuve_confirmation import EpreuveConfirmationRepository
from .event_handlers import reagir_a_approbation_admission
from .repository.parcours_doctoral import ParcoursDoctoralRepository
from ...ddd.use_case.write.initialiser_parcours_doctoral import initialiser_parcours_doctoral

COMMAND_HANDLERS = {
    RecupererParcoursDoctoralQuery: lambda msg_bus, cmd: recuperer_parcours_doctoral(
        cmd,
        parcours_doctoral_repository=ParcoursDoctoralRepository(),
    ),
    EnvoyerMessageDoctorantCommand: lambda msg_bus, cmd: envoyer_message_au_doctorant(
        cmd,
        parcours_doctoral_repository=ParcoursDoctoralRepository(),
        notification=Notification(),
        historique=Historique(),
    ),
    InitialiserParcoursDoctoralCommand: lambda msg_bus, cmd: initialiser_parcours_doctoral(
        cmd,
        proposition_repository=PropositionRepository(),
        parcours_doctoral_repository=ParcoursDoctoralRepository(),
        groupe_de_supervision_repository=GroupeDeSupervisionRepository(),
        epreuve_confirmation_repository=EpreuveConfirmationRepository(),
        historique=Historique(),
    ),
}

EVENT_HANDLERS = {
    InscriptionDoctoraleApprouveeParSicEvent: [reagir_a_approbation_admission.process],
    AdmissionDoctoraleApprouveeParSicEvent: [reagir_a_approbation_admission.process],
}
