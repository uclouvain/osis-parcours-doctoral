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
from parcours_doctoral.ddd.autorisation_diffusion_these.commands import (
    RefuserTheseParScebCommand,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.builder.identity_builder import (
    AutorisationDiffusionTheseIdentityBuilder,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.autorisation_diffusion_these import (
    AutorisationDiffusionTheseIdentity,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.service.i_notification import (
    INotification,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.repository.i_autorisation_diffusion_these import (
    IAutorisationDiffusionTheseRepository,
)


def refuser_these_par_sceb(
    cmd: RefuserTheseParScebCommand,
    autorisation_diffusion_these_repository: IAutorisationDiffusionTheseRepository,
    notification: INotification,
) -> AutorisationDiffusionTheseIdentity:
    identity = AutorisationDiffusionTheseIdentityBuilder.build_from_uuid(uuid=cmd.uuid_parcours_doctoral)
    entity = autorisation_diffusion_these_repository.get(identity)

    entity.refuser_these_par_sceb(
        matricule_sceb=cmd.matricule_sceb,
        motif_refus=cmd.motif_refus,
        commentaire_interne=cmd.commentaire_interne,
        commentaire_externe=cmd.commentaire_externe,
    )

    autorisation_diffusion_these_repository.save(entity)

    notification.refuser_these_par_sceb(autorisation_diffusion_these=entity)

    return identity
