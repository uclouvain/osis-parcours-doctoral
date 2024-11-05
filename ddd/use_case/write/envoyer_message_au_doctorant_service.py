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

from parcours_doctoral.ddd.builder.parcours_doctoral_identity import ParcoursDoctoralIdentityBuilder
from parcours_doctoral.ddd.commands import EnvoyerMessageDoctorantCommand
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoralIdentity
from parcours_doctoral.ddd.domain.service.i_historique import IHistorique
from parcours_doctoral.ddd.domain.service.i_notification import INotification
from parcours_doctoral.ddd.repository.i_parcours_doctoral import IParcoursDoctoralRepository


def envoyer_message_au_doctorant(
    cmd: 'EnvoyerMessageDoctorantCommand',
    parcours_doctoral_repository: 'IParcoursDoctoralRepository',
    notification: 'INotification',
    historique: 'IHistorique',
) -> 'ParcoursDoctoralIdentity':
    # GIVEN
    parcours_doctoral_identity = ParcoursDoctoralIdentityBuilder.build_from_uuid(cmd.parcours_doctoral_uuid)
    parcours_doctoral = parcours_doctoral_repository.get(entity_id=parcours_doctoral_identity)

    # THEN
    message = notification.envoyer_message(
        parcours_doctoral,
        cmd.matricule_emetteur,
        parcours_doctoral.matricule_doctorant,
        cmd.sujet,
        cmd.message,
        cmd.cc_promoteurs,
        cmd.cc_membres_ca,
    )
    historique.historiser_message_au_doctorant(parcours_doctoral, cmd.matricule_emetteur, message)

    return parcours_doctoral_identity
