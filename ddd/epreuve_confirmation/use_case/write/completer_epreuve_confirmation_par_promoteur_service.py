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
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.epreuve_confirmation.builder.epreuve_confirmation_identity import (
    EpreuveConfirmationIdentityBuilder,
)
from parcours_doctoral.ddd.epreuve_confirmation.commands import (
    CompleterEpreuveConfirmationParPromoteurCommand,
)
from parcours_doctoral.ddd.epreuve_confirmation.domain.service.i_notification import (
    INotification,
)
from parcours_doctoral.ddd.epreuve_confirmation.repository.i_epreuve_confirmation import (
    IEpreuveConfirmationRepository,
)


def completer_epreuve_confirmation_par_promoteur(
    cmd: 'CompleterEpreuveConfirmationParPromoteurCommand',
    epreuve_confirmation_repository: 'IEpreuveConfirmationRepository',
    notification: 'INotification',
) -> ParcoursDoctoralIdentity:
    # GIVEN
    epreuve_confirmation_id = EpreuveConfirmationIdentityBuilder.build_from_uuid(cmd.uuid)
    epreuve_confirmation = epreuve_confirmation_repository.get(epreuve_confirmation_id)

    # WHEN
    epreuve_confirmation.completer_par_promoteur(
        proces_verbal_ca=cmd.proces_verbal_ca,
        avis_renouvellement_mandat_recherche=cmd.avis_renouvellement_mandat_recherche,
    )

    # THEN
    notification.notifier_completion_par_promoteur(epreuve_confirmation=epreuve_confirmation)
    epreuve_confirmation_repository.save(epreuve_confirmation)

    return epreuve_confirmation.parcours_doctoral_id
