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
from parcours_doctoral.ddd.builder.parcours_doctoral_identity import (
    ParcoursDoctoralIdentityBuilder,
)
from parcours_doctoral.ddd.commands import DemanderSignaturesCommand
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.domain.service.i_historique import IHistorique
from parcours_doctoral.ddd.domain.service.i_notification import INotification
from parcours_doctoral.ddd.domain.service.i_promoteur import IPromoteurTranslator
from parcours_doctoral.ddd.domain.service.verifier_cotutelle import (
    CotutellePossedePromoteurExterne,
)
from parcours_doctoral.ddd.domain.service.verifier_promoteur import (
    GroupeDeSupervisionPossedeUnPromoteurMinimum,
)
from parcours_doctoral.ddd.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from parcours_doctoral.ddd.repository.i_parcours_doctoral import (
    IParcoursDoctoralRepository,
)


def demander_signatures(
    cmd: 'DemanderSignaturesCommand',
    parcours_doctoral_repository: 'IParcoursDoctoralRepository',
    groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
    promoteur_translator: 'IPromoteurTranslator',
    historique: 'IHistorique',
    notification: 'INotification',
) -> 'ParcoursDoctoralIdentity':
    # GIVEN
    entity_id = ParcoursDoctoralIdentityBuilder.build_from_uuid(cmd.uuid_parcours_doctoral)
    parcours_doctoral = parcours_doctoral_repository.get(entity_id=entity_id)
    groupe_de_supervision = groupe_supervision_repository.get_by_parcours_doctoral_id(entity_id)
    GroupeDeSupervisionPossedeUnPromoteurMinimum().verifier(groupe_de_supervision, promoteur_translator)
    CotutellePossedePromoteurExterne().verifier(parcours_doctoral, groupe_de_supervision, promoteur_translator)
    parcours_doctoral.verifier_projet_doctoral()
    groupe_de_supervision.verifier_signataires()

    # WHEN
    parcours_doctoral.verrouiller_parcours_doctoral_pour_signature()
    groupe_de_supervision.verrouiller_groupe_pour_signature()
    groupe_de_supervision.inviter_a_signer()

    # THEN
    groupe_supervision_repository.save(groupe_de_supervision)
    parcours_doctoral_repository.save(parcours_doctoral)
    notification.envoyer_signatures(parcours_doctoral, groupe_de_supervision)
    historique.historiser_demande_signatures(parcours_doctoral, cmd.matricule_auteur)

    return parcours_doctoral.entity_id
