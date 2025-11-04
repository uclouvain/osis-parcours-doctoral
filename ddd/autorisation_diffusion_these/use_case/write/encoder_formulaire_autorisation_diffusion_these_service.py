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
    EncoderFormulaireAutorisationDiffusionTheseCommand,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.builder.identity_builder import (
    AutorisationDiffusionTheseIdentityBuilder,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.autorisation_diffusion_these import (
    AutorisationDiffusionTheseIdentity,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.repository.i_autorisation_diffusion_these import (
    IAutorisationDiffusionTheseRepository,
)


def encoder_formulaire_autorisation_diffusion_these(
    cmd: EncoderFormulaireAutorisationDiffusionTheseCommand,
    autorisation_diffusion_these_repository: IAutorisationDiffusionTheseRepository,
) -> AutorisationDiffusionTheseIdentity:
    identity = AutorisationDiffusionTheseIdentityBuilder.build_from_uuid(uuid=cmd.uuid_parcours_doctoral)
    entity = autorisation_diffusion_these_repository.get(identity)

    entity.encoder_formulaire(
        sources_financement=cmd.sources_financement,
        resume_anglais=cmd.resume_anglais,
        resume_autre_langue=cmd.resume_autre_langue,
        langue_redaction_these=cmd.langue_redaction_these,
        mots_cles=cmd.mots_cles,
        type_modalites_diffusion=cmd.type_modalites_diffusion,
        date_embargo=cmd.date_embargo,
        limitations_additionnelles_chapitres=cmd.limitations_additionnelles_chapitres,
        modalites_diffusion_acceptees=cmd.modalites_diffusion_acceptees,
    )

    autorisation_diffusion_these_repository.save(entity)

    return identity
