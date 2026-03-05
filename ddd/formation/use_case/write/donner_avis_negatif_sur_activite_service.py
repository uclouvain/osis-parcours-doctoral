# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from parcours_doctoral.ddd.formation.builder.activite_identity_builder import (
    ActiviteIdentityBuilder,
)
from parcours_doctoral.ddd.formation.commands import DonnerAvisNegatifSurActiviteCommand
from parcours_doctoral.ddd.formation.domain.model.activite import ActiviteIdentity
from parcours_doctoral.ddd.formation.domain.service.i_notification import INotification
from parcours_doctoral.ddd.formation.repository.i_activite import IActiviteRepository


def donner_avis_negatif_sur_activite(
    cmd: 'DonnerAvisNegatifSurActiviteCommand',
    activite_repository: 'IActiviteRepository',
    parcours_doctoral_repository: 'IParcoursDoctoralRepository',
    notification: 'INotification',
) -> 'ActiviteIdentity':
    # GIVEN
    parcours_doctoral_id = ParcoursDoctoralIdentityBuilder.build_from_uuid(cmd.parcours_doctoral_uuid)
    parcours_doctoral = parcours_doctoral_repository.get(parcours_doctoral_id)
    activite_id = ActiviteIdentityBuilder.build_from_uuid(cmd.activite_uuid)
    activite = activite_repository.get(activite_id)

    # WHEN

    # THEN
    activite.donner_avis_negatif_promoteur_reference(cmd.commentaire)
    activite_repository.save(activite)
    notification.notifier_avis_negatif_par_promoteur_au_candidat(parcours_doctoral, activite)

    return activite_id
