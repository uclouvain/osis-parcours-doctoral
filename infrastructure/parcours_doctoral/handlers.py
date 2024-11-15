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
from admission.infrastructure.admission.doctorat.preparation.repository.groupe_de_supervision import (
    GroupeDeSupervisionRepository,
)
from admission.ddd.admission.doctorat.events import (
    InscriptionDoctoraleApprouveeParSicEvent,
    AdmissionDoctoraleApprouveeParSicEvent,
)
from admission.infrastructure.admission.doctorat.preparation.repository.proposition import PropositionRepository
from parcours_doctoral.ddd.commands import *
from parcours_doctoral.ddd.use_case.read import *
from parcours_doctoral.ddd.use_case.write import *
from .domain.service.historique import Historique
from .domain.service.membre_CA import MembreCATranslator
from .domain.service.notification import Notification
from .domain.service.promoteur import PromoteurTranslator
from .epreuve_confirmation.repository.epreuve_confirmation import EpreuveConfirmationRepository
from .event_handlers import reagir_a_approbation_admission
from .repository.groupe_de_supervision import GroupeDeSupervisionRepository
from .repository.parcours_doctoral import ParcoursDoctoralRepository
from ...ddd.use_case.read.recuperer_groupe_de_supervision_service import recuperer_groupe_de_supervision
from ...ddd.use_case.write.demander_signatures_service import demander_signatures
from ...ddd.use_case.write.designer_promoteur_reference_service import designer_promoteur_reference
from ...ddd.use_case.write.identifier_membre_CA_service import identifier_membre_ca
from ...ddd.use_case.write.identifier_promoteur_service import identifier_promoteur
from ...ddd.use_case.write.initialiser_parcours_doctoral import initialiser_parcours_doctoral
from ...ddd.use_case.write.modifier_membre_supervision_externe_service import modifier_membre_supervision_externe
from ...ddd.use_case.write.renvoyer_invitation_signature_externe_service import renvoyer_invitation_signature_externe
from ...ddd.use_case.write.supprimer_membre_CA_service import supprimer_membre_CA
from ...ddd.use_case.write.supprimer_promoteur_service import supprimer_promoteur

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
    ListerParcoursDoctorauxDoctorantQuery: lambda msg_bus, cmd: lister_parcours_doctoraux_doctorant(
        cmd,
        parcours_doctoral_repository=ParcoursDoctoralRepository(),
    ),
    ListerParcoursDoctorauxSupervisesQuery: lambda msg_bus, cmd: lister_parcours_doctoraux_supervises(
        cmd,
        parcours_doctoral_repository=ParcoursDoctoralRepository(),
    ),
    ModifierProjetCommand: lambda msg_bus, cmd: modifier_projet(
        cmd,
        parcours_doctoral_repository=ParcoursDoctoralRepository(),
        historique=Historique(),
    ),
    ModifierFinancementCommand: lambda msg_bus, cmd: modifier_financement(
        cmd,
        parcours_doctoral_repository=ParcoursDoctoralRepository(),
        historique=Historique(),
    ),
    IdentifierPromoteurCommand: lambda msg_bus, cmd: identifier_promoteur(
        cmd,
        parcours_doctoral_repository=ParcoursDoctoralRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        promoteur_translator=PromoteurTranslator(),
        historique=Historique(),
    ),
    IdentifierMembreCACommand: lambda msg_bus, cmd: identifier_membre_ca(
        cmd,
        parcours_doctoral_repository=ParcoursDoctoralRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        membre_ca_translator=MembreCATranslator(),
        historique=Historique(),
    ),
    ModifierMembreSupervisionExterneCommand: lambda msg_bus, cmd: modifier_membre_supervision_externe(
        cmd,
        parcours_doctoral_repository=ParcoursDoctoralRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        promoteur_translator=PromoteurTranslator(),
        membre_ca_translator=MembreCATranslator(),
        historique=Historique(),
    ),
    DemanderSignaturesCommand: lambda msg_bus, cmd: demander_signatures(
        cmd,
        parcours_doctoral_repository=ParcoursDoctoralRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        promoteur_translator=PromoteurTranslator(),
        historique=Historique(),
        notification=Notification(),
    ),
    RenvoyerInvitationSignatureExterneCommand: lambda msg_bus, cmd: renvoyer_invitation_signature_externe(
        cmd,
        parcours_doctoral_repository=ParcoursDoctoralRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        notification=Notification(),
    ),
    SupprimerPromoteurCommand: lambda msg_bus, cmd: supprimer_promoteur(
        cmd,
        parcours_doctoral_repository=ParcoursDoctoralRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        historique=Historique(),
        notification=Notification(),
    ),
    DesignerPromoteurReferenceCommand: lambda msg_bus, cmd: designer_promoteur_reference(
        cmd,
        parcours_doctoral_repository=ParcoursDoctoralRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        historique=Historique(),
    ),
    SupprimerMembreCACommand: lambda msg_bus, cmd: supprimer_membre_CA(
        cmd,
        parcours_doctoral_repository=ParcoursDoctoralRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        historique=Historique(),
        notification=Notification(),
    ),
    GetGroupeDeSupervisionCommand: lambda msg_bus, cmd: recuperer_groupe_de_supervision(
        cmd,
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        promoteur_translator=PromoteurTranslator(),
        membre_ca_translator=MembreCATranslator(),
    ),
    ModifierCotutelleCommand: lambda msg_bus, cmd: modifier_cotutelle(
        cmd,
        parcours_doctoral_repository=ParcoursDoctoralRepository(),
        historique=Historique(),
    ),
}

EVENT_HANDLERS = {
    InscriptionDoctoraleApprouveeParSicEvent: [reagir_a_approbation_admission.process],
    AdmissionDoctoraleApprouveeParSicEvent: [reagir_a_approbation_admission.process],
}
