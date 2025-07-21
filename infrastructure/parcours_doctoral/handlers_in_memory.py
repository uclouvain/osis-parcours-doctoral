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
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from infrastructure.parcours_interne.domain.service.in_memory.pae import (
    InMemoryPaeTranslator,
)
from parcours_doctoral.ddd.commands import *
from parcours_doctoral.ddd.commands import ListerDocumentsQuery, RecupererDocumentQuery
from parcours_doctoral.ddd.use_case.read import *
from parcours_doctoral.ddd.use_case.read.get_cotutelle_service import get_cotutelle
from parcours_doctoral.ddd.use_case.read.recuperer_groupe_de_supervision_service import (
    recuperer_groupe_de_supervision,
)
from parcours_doctoral.ddd.use_case.write import *
from parcours_doctoral.ddd.use_case.write.approuver_membre_par_pdf_service import (
    approuver_membre_par_pdf,
)
from parcours_doctoral.ddd.use_case.write.demander_signatures_service import (
    demander_signatures,
)
from parcours_doctoral.ddd.use_case.write.designer_promoteur_reference_service import (
    designer_promoteur_reference,
)
from parcours_doctoral.ddd.use_case.write.generer_pdf_archive_service import (
    generer_pdf_archive,
)
from parcours_doctoral.ddd.use_case.write.identifier_membre_CA_service import (
    identifier_membre_ca,
)
from parcours_doctoral.ddd.use_case.write.identifier_promoteur_service import (
    identifier_promoteur,
)
from parcours_doctoral.ddd.use_case.write.initialiser_parcours_doctoral import (
    initialiser_parcours_doctoral,
)
from parcours_doctoral.ddd.use_case.write.modifier_membre_supervision_externe_service import (
    modifier_membre_supervision_externe,
)
from parcours_doctoral.ddd.use_case.write.renvoyer_invitation_signature_externe_service import (
    renvoyer_invitation_signature_externe,
)
from parcours_doctoral.ddd.use_case.write.supprimer_membre_CA_service import (
    supprimer_membre_CA,
)
from parcours_doctoral.ddd.use_case.write.supprimer_promoteur_service import (
    supprimer_promoteur,
)
from parcours_doctoral.infrastructure.parcours_doctoral.defense_privee.repository.in_memory.defense_privee import (
    DefensePriveeInMemoryRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.domain.service.in_memory.historique import (
    HistoriqueInMemory,
)
from parcours_doctoral.infrastructure.parcours_doctoral.domain.service.in_memory.membre_CA import (
    MembreCAInMemoryTranslator,
)
from parcours_doctoral.infrastructure.parcours_doctoral.domain.service.in_memory.notification import (
    NotificationInMemory,
)
from parcours_doctoral.infrastructure.parcours_doctoral.domain.service.in_memory.parcours_doctoral import (
    ParcoursDoctoralInMemoryService,
)
from parcours_doctoral.infrastructure.parcours_doctoral.domain.service.in_memory.pdf_generation import (
    InMemoryPDFGeneration,
)
from parcours_doctoral.infrastructure.parcours_doctoral.domain.service.in_memory.promoteur import (
    PromoteurInMemoryTranslator,
)
from parcours_doctoral.infrastructure.parcours_doctoral.epreuve_confirmation.repository.in_memory.epreuve_confirmation import (
    EpreuveConfirmationInMemoryRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.formation.repository.in_memory.activite import (
    ActiviteInMemoryRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.jury.repository.in_memory.jury import (
    JuryInMemoryRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.read_view.handlers_in_memory import (
    COMMAND_HANDLERS as READ_VIEW_COMMAND_HANDLERS,
)
from parcours_doctoral.infrastructure.parcours_doctoral.repository.in_memory.document import (
    DocumentInMemoryRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.repository.in_memory.parcours_doctoral import (
    ParcoursDoctoralInMemoryRepository,
)

_parcours_doctoral_repository = ParcoursDoctoralInMemoryRepository()
_parcours_doctoral_service = ParcoursDoctoralInMemoryService()
_epreuve_confirmation_repository = EpreuveConfirmationInMemoryRepository()
_defense_privee_repository = DefensePriveeInMemoryRepository()
_proposition_repository = PropositionInMemoryRepository()
_groupe_de_supervision_repository = GroupeDeSupervisionInMemoryRepository()
_notification = NotificationInMemory()
_historique = HistoriqueInMemory()
_membre_ca_translator = MembreCAInMemoryTranslator()
_promoteur_translator = PromoteurInMemoryTranslator()
_document_repository = DocumentInMemoryRepository()
_pdf_generation_service = InMemoryPDFGeneration()
_jury_repository = JuryInMemoryRepository()
_activite_repository = ActiviteInMemoryRepository()
_pae_translator = InMemoryPaeTranslator()


COMMAND_HANDLERS = {
    RecupererParcoursDoctoralQuery: lambda msg_bus, cmd: recuperer_parcours_doctoral(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
    ),
    RecupererParcoursDoctoralPropositionQuery: lambda msg_bus, cmd: recuperer_parcours_doctoral_proposition(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
    ),
    GetCotutelleQuery: lambda msg_bus, cmd: get_cotutelle(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
    ),
    EnvoyerMessageDoctorantCommand: lambda msg_bus, cmd: envoyer_message_au_doctorant(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        notification=_notification,
        historique=_historique,
    ),
    InitialiserParcoursDoctoralCommand: lambda msg_bus, cmd: initialiser_parcours_doctoral(
        cmd,
        proposition_repository=_proposition_repository,
        epreuve_confirmation_repository=_epreuve_confirmation_repository,
        defense_privee_repository=_defense_privee_repository,
        parcours_doctoral_service=_parcours_doctoral_service,
        historique=_historique,
    ),
    ListerParcoursDoctorauxDoctorantQuery: lambda msg_bus, cmd: lister_parcours_doctoraux_doctorant(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
    ),
    ListerParcoursDoctorauxSupervisesQuery: lambda msg_bus, cmd: lister_parcours_doctoraux_supervises(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
    ),
    ModifierProjetCommand: lambda msg_bus, cmd: modifier_projet(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        historique=_historique,
    ),
    ModifierFinancementCommand: lambda msg_bus, cmd: modifier_financement(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        historique=_historique,
    ),
    IdentifierPromoteurCommand: lambda msg_bus, cmd: identifier_promoteur(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        groupe_supervision_repository=_groupe_de_supervision_repository,
        promoteur_translator=_promoteur_translator,
        historique=_historique,
    ),
    IdentifierMembreCACommand: lambda msg_bus, cmd: identifier_membre_ca(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        groupe_supervision_repository=_groupe_de_supervision_repository,
        membre_ca_translator=_membre_ca_translator,
        historique=_historique,
    ),
    ModifierMembreSupervisionExterneCommand: lambda msg_bus, cmd: modifier_membre_supervision_externe(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        groupe_supervision_repository=_groupe_de_supervision_repository,
        promoteur_translator=_promoteur_translator,
        membre_ca_translator=_membre_ca_translator,
        historique=_historique,
    ),
    DemanderSignaturesCommand: lambda msg_bus, cmd: demander_signatures(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        groupe_supervision_repository=_groupe_de_supervision_repository,
        promoteur_translator=_promoteur_translator,
        historique=_historique,
        notification=_notification,
    ),
    RenvoyerInvitationSignatureExterneCommand: lambda msg_bus, cmd: renvoyer_invitation_signature_externe(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        groupe_supervision_repository=_groupe_de_supervision_repository,
        notification=_notification,
    ),
    SupprimerPromoteurCommand: lambda msg_bus, cmd: supprimer_promoteur(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        groupe_supervision_repository=_groupe_de_supervision_repository,
        historique=_historique,
        notification=_notification,
    ),
    DesignerPromoteurReferenceCommand: lambda msg_bus, cmd: designer_promoteur_reference(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        groupe_supervision_repository=_groupe_de_supervision_repository,
        historique=_historique,
    ),
    SupprimerMembreCACommand: lambda msg_bus, cmd: supprimer_membre_CA(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        groupe_supervision_repository=_groupe_de_supervision_repository,
        historique=_historique,
        notification=_notification,
    ),
    GetGroupeDeSupervisionQuery: lambda msg_bus, cmd: recuperer_groupe_de_supervision(
        cmd,
        groupe_supervision_repository=_groupe_de_supervision_repository,
        promoteur_translator=_promoteur_translator,
        membre_ca_translator=_membre_ca_translator,
    ),
    ModifierCotutelleCommand: lambda msg_bus, cmd: modifier_cotutelle(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        historique=_historique,
    ),
    ApprouverMembreParPdfCommand: lambda msg_bus, cmd: approuver_membre_par_pdf(
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        groupe_supervision_repository=_groupe_de_supervision_repository,
        historique=_historique,
    ),
    InitialiserDocumentCommand: lambda msg_bus, cmd: initialiser_document(
        cmd,
        document_repository=_document_repository,
    ),
    ModifierDocumentCommand: lambda msg_bus, cmd: modifier_document(
        cmd,
        document_repository=_document_repository,
    ),
    SupprimerDocumentCommand: lambda msg_bus, cmd: supprimer_document(
        cmd,
        document_repository=_document_repository,
    ),
    ListerDocumentsQuery: lambda msg_bus, cmd: lister_documents(
        cmd,
        document_repository=_document_repository,
    ),
    RecupererDocumentQuery: lambda msg_bus, cmd: recuperer_document(
        cmd,
        document_repository=_document_repository,
    ),
    GenererPdfArchiveCommand: lambda msg_bus, cmd: generer_pdf_archive(
        msg_bus,
        cmd,
        parcours_doctoral_repository=_parcours_doctoral_repository,
        pdf_generation_service=_pdf_generation_service,
        groupe_supervision_repository=_groupe_de_supervision_repository,
        promoteur_translator=_promoteur_translator,
        membre_ca_translator=_membre_ca_translator,
        epreuve_confirmation_repository=_epreuve_confirmation_repository,
        jury_repository=_jury_repository,
        activite_repository=_activite_repository,
        document_repository=_document_repository,
        pae_translator=_pae_translator,
    ),
    **READ_VIEW_COMMAND_HANDLERS,
}
