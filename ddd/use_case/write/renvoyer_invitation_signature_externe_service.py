# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

from parcours_doctoral.ddd.builder.parcours_doctoral_identity import ParcoursDoctoralIdentityBuilder
from parcours_doctoral.ddd.commands import RenvoyerInvitationSignatureExterneCommand
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoralIdentity
from parcours_doctoral.ddd.domain.service.i_notification import INotification
from parcours_doctoral.ddd.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from parcours_doctoral.ddd.repository.i_parcours_doctoral import IParcoursDoctoralRepository


def renvoyer_invitation_signature_externe(
    cmd: 'RenvoyerInvitationSignatureExterneCommand',
    proposition_repository: 'IParcoursDoctoralRepository',
    groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
    notification: 'INotification',
) -> 'ParcoursDoctoralIdentity':
    # GIVEN
    proposition_id = ParcoursDoctoralIdentityBuilder.build_from_uuid(cmd.uuid_proposition)
    proposition_candidat = proposition_repository.get(entity_id=proposition_id)
    groupe_supervision = groupe_supervision_repository.get_by_parcours_doctoral_id(proposition_id)
    membre = groupe_supervision.get_signataire(cmd.uuid_membre)

    # THEN
    notification.renvoyer_invitation(proposition_candidat, membre)

    return proposition_id
