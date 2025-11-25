##############################################################################
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
##############################################################################
from parcours_doctoral.ddd.autorisation_diffusion_these.commands import *
from parcours_doctoral.ddd.autorisation_diffusion_these.use_case.read import *
from parcours_doctoral.ddd.autorisation_diffusion_these.use_case.write import *

from .domain.service.in_memory.notification import NotificationInMemory
from .domain.service.in_memory.signataires_initiaux_autorisation_diffusion_these_service import (
    SignatairesInitiauxAutorisationDiffusionTheseInMemoryService,
)
from .repository.in_memory.autorisation_diffusion_these import (
    AutorisationDiffusionTheseInMemoryRepository,
)

_autorisation_diffusion_these_repository = AutorisationDiffusionTheseInMemoryRepository()
_fgs_signataires_initiaux_autorisation_difussion_these_service = (
    SignatairesInitiauxAutorisationDiffusionTheseInMemoryService()
)
_notification = NotificationInMemory()


COMMAND_HANDLERS = {
    RecupererAutorisationDiffusionTheseQuery: lambda msg_bus, cmd: recuperer_autorisation_diffusion_these(
        cmd,
        autorisation_diffusion_these_repository=_autorisation_diffusion_these_repository,
    ),
    EncoderFormulaireAutorisationDiffusionTheseCommand: (
        lambda msg_bus, cmd: encoder_formulaire_autorisation_diffusion_these(
            cmd,
            autorisation_diffusion_these_repository=_autorisation_diffusion_these_repository,
        )
    ),
    EnvoyerFormulaireAutorisationDiffusionTheseAuPromoteurReferenceCommand: (
        lambda msg_bus, cmd: envoyer_formulaire_autorisation_diffusion_these_au_promoteur_reference(
            cmd,
            autorisation_diffusion_these_repository=_autorisation_diffusion_these_repository,
            signataires_initiaux_autorisation_diffusion_these_service=_fgs_signataires_initiaux_autorisation_difussion_these_service,  # noqa: E501
            notification=_notification,
        )
    ),
    RefuserTheseParPromoteurReferenceCommand: (
        lambda msg_bus, cmd: refuser_these_par_promoteur_reference(
            cmd,
            autorisation_diffusion_these_repository=_autorisation_diffusion_these_repository,
            notification=_notification,
        )
    ),
    AccepterTheseParPromoteurReferenceCommand: (
        lambda msg_bus, cmd: accepter_these_par_promoteur_reference(
            cmd,
            autorisation_diffusion_these_repository=_autorisation_diffusion_these_repository,
            signataires_initiaux_autorisation_diffusion_these_service=_fgs_signataires_initiaux_autorisation_difussion_these_service,  # noqa: E501
            notification=_notification,
        )
    ),
    RefuserTheseParAdreCommand: (
        lambda msg_bus, cmd: refuser_these_par_adre(
            cmd,
            autorisation_diffusion_these_repository=_autorisation_diffusion_these_repository,
            notification=_notification,
        )
    ),
    AccepterTheseParAdreCommand: (
        lambda msg_bus, cmd: accepter_these_par_adre(
            cmd,
            autorisation_diffusion_these_repository=_autorisation_diffusion_these_repository,
            signataires_initiaux_autorisation_diffusion_these_service=_fgs_signataires_initiaux_autorisation_difussion_these_service,  # noqa: E501
            notification=_notification,
        )
    ),
    RefuserTheseParScebCommand: (
        lambda msg_bus, cmd: refuser_these_par_sceb(
            cmd,
            autorisation_diffusion_these_repository=_autorisation_diffusion_these_repository,
            notification=_notification,
        )
    ),
}
