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
import datetime
from typing import Optional

from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixTypeAdmission
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    Proposition,
)
from parcours_doctoral.ddd.builder.parcours_doctoral_identity import (
    ParcoursDoctoralIdentityBuilder,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.domain.service.i_parcours_doctoral import (
    IParcoursDoctoralService,
)
from parcours_doctoral.ddd.epreuve_confirmation.domain.service.epreuve_confirmation import EpreuveConfirmationService
from parcours_doctoral.ddd.epreuve_confirmation.repository.i_epreuve_confirmation import (
    IEpreuveConfirmationRepository,
)


class ParcoursDoctoralInMemoryService(IParcoursDoctoralService):
    @classmethod
    def initier(
        cls,
        proposition: 'Proposition',
        epreuve_confirmation_repository: 'IEpreuveConfirmationRepository',
        date_reference_pour_date_limite_confirmation: Optional[datetime.date] = None,
    ) -> ParcoursDoctoralIdentity:
        parcours_doctoral_identity = ParcoursDoctoralIdentityBuilder.build_from_uuid(uuid=proposition.entity_id.uuid)

        if proposition.type_admission == ChoixTypeAdmission.ADMISSION:
            epreuve_confirmation = EpreuveConfirmationService.initier(
                parcours_doctoral_id=parcours_doctoral_identity,
                date_reference_pour_date_limite=date_reference_pour_date_limite_confirmation,
            )
            epreuve_confirmation_repository.save(entity=epreuve_confirmation)

        return parcours_doctoral_identity
