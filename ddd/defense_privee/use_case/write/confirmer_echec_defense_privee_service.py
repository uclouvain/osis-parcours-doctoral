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
from parcours_doctoral.ddd.defense_privee.commands import (
    ConfirmerEchecDefensePriveeCommand,
)
from parcours_doctoral.ddd.defense_privee.repository.i_defense_privee import (
    IDefensePriveeRepository,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.domain.service.i_historique import IHistorique
from parcours_doctoral.ddd.domain.service.i_notification import INotification
from parcours_doctoral.ddd.repository.i_parcours_doctoral import (
    IParcoursDoctoralRepository,
)


def confirmer_echec_defense_privee(
    cmd: 'ConfirmerEchecDefensePriveeCommand',
    parcours_doctoral_repository: 'IParcoursDoctoralRepository',
    defense_privee_repository: 'IDefensePriveeRepository',
    historique: 'IHistorique',
    notification: 'INotification',
) -> ParcoursDoctoralIdentity:
    # GIVEN
    parcours_doctoral_identity = ParcoursDoctoralIdentity(uuid=cmd.parcours_doctoral_uuid)
    parcours_doctoral = parcours_doctoral_repository.get(parcours_doctoral_identity)

    defense_privee = defense_privee_repository.get_active_dto_by_parcours_doctoral_identity(parcours_doctoral_identity)

    # WHEN
    parcours_doctoral.confirmer_echec_defense_privee(defense_privee=defense_privee)

    # THEN
    parcours_doctoral_repository.save(parcours_doctoral)

    notification.envoyer_message(
        parcours_doctoral=parcours_doctoral,
        matricule_emetteur=cmd.matricule_auteur,
        matricule_doctorant=parcours_doctoral.matricule_doctorant,
        sujet=cmd.sujet_message,
        message=cmd.corps_message,
        cc_promoteurs=False,
        cc_membres_ca=False,
        cc_jury=True,
    )

    historique.historiser_decision_echec_defense_privee(
        parcours_doctoral=parcours_doctoral,
        matricule_auteur=cmd.matricule_auteur,
    )

    return parcours_doctoral_identity
