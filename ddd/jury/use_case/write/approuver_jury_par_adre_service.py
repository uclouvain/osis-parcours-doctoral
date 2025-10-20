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
from parcours_doctoral.ddd.builder.parcours_doctoral_identity import (
    ParcoursDoctoralIdentityBuilder,
)
from parcours_doctoral.ddd.jury.builder.jury_identity_builder import JuryIdentityBuilder
from parcours_doctoral.ddd.jury.commands import ApprouverJuryParAdreCommand
from parcours_doctoral.ddd.jury.domain.model.jury import JuryIdentity
from parcours_doctoral.ddd.jury.domain.service.avis import Avis
from parcours_doctoral.ddd.jury.domain.service.i_historique import IHistorique
from parcours_doctoral.ddd.jury.domain.service.i_jury import IJuryService
from parcours_doctoral.ddd.jury.domain.service.i_notification import INotification
from parcours_doctoral.ddd.jury.domain.service.i_verifier_modification_role import (
    IVerifierModificationRoleService,
)
from parcours_doctoral.ddd.jury.repository.i_jury import IJuryRepository
from parcours_doctoral.ddd.repository.i_parcours_doctoral import (
    IParcoursDoctoralRepository,
)


def approuver_jury_par_adre(
    cmd: 'ApprouverJuryParAdreCommand',
    parcours_doctoral_repository: 'IParcoursDoctoralRepository',
    verifier_modification_role_service: 'IVerifierModificationRoleService',
    jury_repository: 'IJuryRepository',
    jury_service: 'IJuryService',
    historique: 'IHistorique',
    notification: 'INotification',
) -> 'JuryIdentity':
    # GIVEN
    entity_id = ParcoursDoctoralIdentityBuilder.build_from_uuid(cmd.uuid_jury)
    parcours_doctoral = parcours_doctoral_repository.get(entity_id=entity_id)
    jury = jury_repository.get(JuryIdentityBuilder.build_from_uuid(cmd.uuid_jury))
    statut_original_parcours_doctoral = parcours_doctoral.statut

    signataire = jury_service.recuperer_gestionnaire_adre(parcours_doctoral.entity_id, cmd.matricule_auteur)
    avis = Avis.construire_approbation(cmd.commentaire_interne, cmd.commentaire_externe)

    # WHEN
    verifier_modification_role_service.verifier_roles_pour_cdd(
        parcours_doctoral_identity=ParcoursDoctoralIdentityBuilder.build_from_uuid(cmd.uuid_jury),
    )
    jury.approuver_par_adre(signataire, cmd.commentaire_interne, cmd.commentaire_externe)
    parcours_doctoral.approuver_jury_par_adre()

    # THEN
    parcours_doctoral_repository.save(parcours_doctoral)
    jury_repository.save(jury)
    historique.historiser_avis(
        parcours_doctoral, signataire, avis, statut_original_parcours_doctoral, cmd.matricule_auteur
    )
    notification.notifier_approbation_adre(parcours_doctoral, signataire, avis)

    return jury.entity_id
