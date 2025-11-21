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

from parcours_doctoral.auth.roles.adre_manager import AdreManager
from parcours_doctoral.auth.roles.sceb_manager import ScebManager
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.service.i_signataires_initiaux_autorisation_diffusion_these_service import (  # noqa: E501
    ISignatairesInitiauxAutorisationDiffusionTheseService,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.validator.exceptions import (
    GestionnaireADRENonTrouveException,
    GestionnaireSCEBNonTrouveException,
    PromoteurReferenceNonTrouveException,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.models import JuryActor


class SignatairesInitiauxAutorisationDiffusionTheseService(ISignatairesInitiauxAutorisationDiffusionTheseService):
    @classmethod
    def recuperer_fgs_gestionnaire_sceb(cls) -> str:
        global_id = ScebManager.objects.values_list('person__global_id', flat=True).first()

        if not global_id:
            raise GestionnaireSCEBNonTrouveException

        return global_id

    @classmethod
    def recuperer_fgs_gestionnaire_adre(cls) -> str:
        global_id = AdreManager.objects.values_list('person__global_id', flat=True).first()

        if not global_id:
            raise GestionnaireADRENonTrouveException

        return global_id

    @classmethod
    def recuperer_fgs_promoteur_reference(cls, parcours_doctoral_id: ParcoursDoctoralIdentity) -> str:
        global_id = (
            JuryActor.objects.filter(
                is_promoter=True,
                is_lead_promoter=True,
                process__doctorate_from_jury_group__uuid=parcours_doctoral_id.uuid,
            )
            .values_list('person__global_id', flat=True)
            .first()
        )

        if not global_id:
            raise PromoteurReferenceNonTrouveException

        return global_id
