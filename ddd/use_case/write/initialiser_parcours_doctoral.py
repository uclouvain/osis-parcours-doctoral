# ##############################################################################
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
# ##############################################################################
from admission.ddd.admission.doctorat.preparation.repository.i_groupe_de_supervision import \
    IGroupeDeSupervisionRepository
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.doctorat.validation.domain.service.proposition_identity import \
    PropositionIdentityTranslator
from parcours_doctoral.ddd.commands import InitialiserParcoursDoctoralCommand
from parcours_doctoral.ddd.domain.service.i_historique import IHistorique
from parcours_doctoral.ddd.domain.service.i_parcours_doctoral import IParcoursDoctoralService
from parcours_doctoral.ddd.epreuve_confirmation.domain.service.epreuve_confirmation import EpreuveConfirmationService
from parcours_doctoral.ddd.epreuve_confirmation.repository.i_epreuve_confirmation import IEpreuveConfirmationRepository
from parcours_doctoral.ddd.repository.i_parcours_doctoral import IParcoursDoctoralRepository


def initialiser_parcours_doctoral(
    cmd: 'InitialiserParcoursDoctoralCommand',
    proposition_repository: 'IPropositionRepository',
    parcours_doctoral_repository: 'IParcoursDoctoralRepository',
    groupe_de_supervision_repository: 'IGroupeDeSupervisionRepository',
    epreuve_confirmation_repository: 'IEpreuveConfirmationRepository',
    parcours_doctoral_service: 'IParcoursDoctoralService',
    historique: 'IHistorique',
) -> 'ParcoursDoctoralIdentity':
    proposition_id = PropositionIdentityTranslator.convertir_depuis_demande(cmd.proposition_uuid)
    proposition = proposition_repository.get(entity_id=proposition_id)

    # WHEN
    epreuve_confirmation = EpreuveConfirmationService.initier(proposition_id=proposition_id)

    # THEN
    parcours_doctoral_entity_id = parcours_doctoral_service.initier(
        proposition=proposition,
    )
    epreuve_confirmation_repository.save(epreuve_confirmation)
    historique.historiser_initialisation(parcours_doctoral_entity_id)

    return parcours_doctoral_entity_id
