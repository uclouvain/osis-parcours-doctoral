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
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoralIdentity
from parcours_doctoral.ddd.epreuve_confirmation.builder.epreuve_confirmation_identity import (
    EpreuveConfirmationIdentityBuilder,
)
from parcours_doctoral.ddd.epreuve_confirmation.commands import (
    ConfirmerReussiteCommand,
)
from parcours_doctoral.ddd.epreuve_confirmation.domain.service.i_notification import INotification
from parcours_doctoral.ddd.epreuve_confirmation.repository.i_epreuve_confirmation import (
    IEpreuveConfirmationRepository,
)
from parcours_doctoral.ddd.repository.i_parcours_doctoral import IParcoursDoctoralRepository


def confirmer_reussite(
    cmd: 'ConfirmerReussiteCommand',
    epreuve_confirmation_repository: 'IEpreuveConfirmationRepository',
    parcours_doctoral_repository: 'IParcoursDoctoralRepository',
    notification: 'INotification',
) -> ParcoursDoctoralIdentity:
    # GIVEN
    epreuve_confirmation_id = EpreuveConfirmationIdentityBuilder.build_from_uuid(cmd.uuid)
    epreuve_confirmation = epreuve_confirmation_repository.get(epreuve_confirmation_id)

    parcours_doctoral = parcours_doctoral_repository.get(epreuve_confirmation.parcours_doctoral_id)

    # WHEN
    epreuve_confirmation.verifier_pour_encodage_decision()
    parcours_doctoral.encoder_decision_reussite_epreuve_confirmation()

    # THEN
    notification.notifier_reussite_epreuve(epreuve_confirmation)
    parcours_doctoral_repository.save(parcours_doctoral)

    return parcours_doctoral.entity_id
