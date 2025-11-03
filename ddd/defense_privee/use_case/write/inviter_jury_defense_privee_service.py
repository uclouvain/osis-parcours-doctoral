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
from ddd.logic.shared_kernel.personne_connue_ucl.domain.service.personne_connue_ucl import (
    IPersonneConnueUclTranslator,
)
from parcours_doctoral.ddd.defense_privee.commands import (
    InviterJuryDefensePriveeCommand,
)
from parcours_doctoral.ddd.defense_privee.domain.service.i_notification import (
    INotification,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.domain.service.i_historique import IHistorique
from parcours_doctoral.ddd.repository.i_parcours_doctoral import (
    IParcoursDoctoralRepository,
)


def inviter_jury_defense_privee(
    cmd: 'InviterJuryDefensePriveeCommand',
    parcours_doctoral_repository: 'IParcoursDoctoralRepository',
    notification: 'INotification',
    personne_connue_ucl_translator: 'IPersonneConnueUclTranslator',
) -> ParcoursDoctoralIdentity:
    # GIVEN
    parcours_doctoral_identity = ParcoursDoctoralIdentity(uuid=cmd.parcours_doctoral_uuid)
    parcours_doctoral = parcours_doctoral_repository.get(parcours_doctoral_identity)
    auteur = personne_connue_ucl_translator.get(matricule=cmd.matricule_auteur)

    # WHEN
    parcours_doctoral.inviter_jury_defense_privee()

    # THEN
    notification.inviter_membres_jury(
        parcours_doctoral=parcours_doctoral,
        auteur=auteur,
    )

    return parcours_doctoral_identity
