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
from uuid import UUID

from ddd.logic.parcours_interne.domain.service.i_pae import IPaeTranslator
from infrastructure.utils import MessageBus
from parcours_doctoral.ddd.builder.document_builder import DocumentBuilder
from parcours_doctoral.ddd.builder.parcours_doctoral_identity import (
    ParcoursDoctoralIdentityBuilder,
)
from parcours_doctoral.ddd.commands import GenererPdfArchiveCommand
from parcours_doctoral.ddd.domain.model.document import DocumentIdentity, TypeDocument
from parcours_doctoral.ddd.domain.service.groupe_de_supervision_dto import (
    GroupeDeSupervisionDto,
)
from parcours_doctoral.ddd.domain.service.i_membre_CA import IMembreCATranslator
from parcours_doctoral.ddd.domain.service.i_pdf_generation import IPDFGeneration
from parcours_doctoral.ddd.domain.service.i_promoteur import IPromoteurTranslator
from parcours_doctoral.ddd.epreuve_confirmation.repository.i_epreuve_confirmation import (
    IEpreuveConfirmationRepository,
)
from parcours_doctoral.ddd.formation.repository.i_activite import IActiviteRepository
from parcours_doctoral.ddd.jury.builder.jury_identity_builder import JuryIdentityBuilder
from parcours_doctoral.ddd.jury.repository.i_jury import IJuryRepository
from parcours_doctoral.ddd.repository.i_document import IDocumentRepository
from parcours_doctoral.ddd.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from parcours_doctoral.ddd.repository.i_parcours_doctoral import (
    IParcoursDoctoralRepository,
)


def generer_pdf_archive(
    msg_bus: 'MessageBus',
    cmd: 'GenererPdfArchiveCommand',
    parcours_doctoral_repository: 'IParcoursDoctoralRepository',
    pdf_generation_service: 'IPDFGeneration',
    groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
    promoteur_translator: 'IPromoteurTranslator',
    membre_ca_translator: 'IMembreCATranslator',
    epreuve_confirmation_repository: 'IEpreuveConfirmationRepository',
    jury_repository: 'IJuryRepository',
    activite_repository: 'IActiviteRepository',
    document_repository: 'IDocumentRepository',
    pae_translator: 'IPaeTranslator',
) -> 'DocumentIdentity':
    # GIVEN
    parcours_doctoral_id = ParcoursDoctoralIdentityBuilder.build_from_uuid(cmd.uuid_parcours_doctoral)
    parcours_doctoral = parcours_doctoral_repository.get_dto(entity_id=parcours_doctoral_id)
    groupe_supervision = GroupeDeSupervisionDto().get(
        uuid_parcours_doctoral=cmd.uuid_parcours_doctoral,
        repository=groupe_supervision_repository,
        promoteur_translator=promoteur_translator,
        membre_ca_translator=membre_ca_translator,
    )
    epreuves_confirmation = epreuve_confirmation_repository.search_dto_by_parcours_doctoral_identity(
        parcours_doctoral_id
    )
    jury = jury_repository.get_dto(JuryIdentityBuilder.build_from_uuid(cmd.uuid_parcours_doctoral))
    cours_complementaires = activite_repository.get_complementaries_training_for_doctoral_training(parcours_doctoral_id)
    proprietes_pae = pae_translator.search_proprietes(
        msg_bus=msg_bus,
        sigle_formation=parcours_doctoral.formation.sigle,
        nomas=[parcours_doctoral.noma_doctorant],
        annee=parcours_doctoral.formation.annee,
        est_premiere_annee_bachelier=False,
    )

    # WHEN

    # THEN
    pdf_uuid = pdf_generation_service.generer_pdf_archive(
        parcours_doctoral=parcours_doctoral,
        groupe_supervision=groupe_supervision,
        epreuves_confirmation=epreuves_confirmation,
        jury=jury,
        cours_complementaires=cours_complementaires,
        proprietes_pae=proprietes_pae,
    )

    document = DocumentBuilder().initialiser_document(
        uuid_parcours_doctoral=cmd.uuid_parcours_doctoral,
        auteur=cmd.auteur,
        libelle='Archive',
        type_document=TypeDocument.SYSTEME.name,
    )
    document.modifier(uuids_documents=[pdf_uuid], auteur=cmd.auteur)
    document_repository.save(document)

    return document.entity_id
