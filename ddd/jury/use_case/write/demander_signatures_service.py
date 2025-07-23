# ##############################################################################
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
# ##############################################################################
from parcours_doctoral.ddd.builder.parcours_doctoral_identity import (
    ParcoursDoctoralIdentityBuilder,
)
from parcours_doctoral.ddd.jury.builder.jury_identity_builder import JuryIdentityBuilder
from parcours_doctoral.ddd.jury.commands import DemanderSignaturesCommand
from parcours_doctoral.ddd.jury.domain.model.jury import JuryIdentity
from parcours_doctoral.ddd.jury.domain.service.i_historique import IHistorique
from parcours_doctoral.ddd.jury.domain.service.i_notification import INotification
from parcours_doctoral.ddd.jury.domain.validator.validator_by_business_action import (
    VerifierJuryConditionSignature,
)
from parcours_doctoral.ddd.jury.repository.i_jury import IJuryRepository
from parcours_doctoral.ddd.repository.i_parcours_doctoral import (
    IParcoursDoctoralRepository,
)


def demander_signatures(
    cmd: 'DemanderSignaturesCommand',
    jury_repository: 'IJuryRepository',
    jury_service: 'IJuryService',
    parcours_doctoral_repository: 'IParcoursDoctoralRepository',
    historique: 'IHistorique',
    notification: 'INotification',
) -> 'JuryIdentity':
    # GIVEN
    entity_id = ParcoursDoctoralIdentityBuilder.build_from_uuid(cmd.uuid_parcours_doctoral)
    parcours_doctoral = parcours_doctoral_repository.get(entity_id=entity_id)
    jury = jury_repository.get(JuryIdentityBuilder.build_from_uuid(cmd.uuid_parcours_doctoral))
    verificateur = jury_service.recuperer_verificateur(entity_id)

    # WHEN
    VerifierJuryConditionSignature(
        jury=jury,
    ).validate()

    parcours_doctoral.verrouiller_jury_pour_signature()
    jury.inviter_a_signer(verificateur)

    # THEN
    jury_repository.save(jury)
    parcours_doctoral_repository.save(parcours_doctoral)
    notification.envoyer_signatures(parcours_doctoral, jury)
    historique.historiser_demande_signatures(parcours_doctoral, jury, cmd.matricule_auteur)

    return jury.entity_id
