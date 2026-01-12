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
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.recevabilite.commands import InviterJuryRecevabiliteCommand
from parcours_doctoral.ddd.recevabilite.domain.service.i_notification import (
    INotification,
)
from parcours_doctoral.ddd.repository.i_parcours_doctoral import (
    IParcoursDoctoralRepository,
)


def inviter_jury_recevabilite(
    cmd: 'InviterJuryRecevabiliteCommand',
    parcours_doctoral_repository: 'IParcoursDoctoralRepository',
    notification: 'INotification',
) -> ParcoursDoctoralIdentity:
    # GIVEN
    parcours_doctoral_identity = ParcoursDoctoralIdentity(uuid=cmd.parcours_doctoral_uuid)
    parcours_doctoral = parcours_doctoral_repository.get(entity_id=parcours_doctoral_identity)

    parcours_doctoral.verifier_invitation_du_jury_a_recevabilite_est_possible()

    # THEN
    notification.inviter_membres_jury(parcours_doctoral_uuid=cmd.parcours_doctoral_uuid)

    return parcours_doctoral_identity
