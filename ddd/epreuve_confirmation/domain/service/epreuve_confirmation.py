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
import datetime
import uuid
from typing import Optional

from dateutil.relativedelta import relativedelta
from osis_common.ddd import interface

from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.epreuve_confirmation.builder.epreuve_confirmation_identity import (
    EpreuveConfirmationIdentityBuilder,
)
from parcours_doctoral.ddd.epreuve_confirmation.domain.model.epreuve_confirmation import (
    EpreuveConfirmation,
)


class EpreuveConfirmationService(interface.DomainService):
    NB_MOIS_INTERVALLE_DATE_LIMITE = 24

    @classmethod
    def initier(
        cls,
        parcours_doctoral_id: 'ParcoursDoctoralIdentity',
        date_limite: Optional[datetime.date] = None,
    ) -> EpreuveConfirmation:
        if not date_limite:
            date_limite = datetime.date.today() + relativedelta(months=cls.NB_MOIS_INTERVALLE_DATE_LIMITE)

        return EpreuveConfirmation(
            entity_id=EpreuveConfirmationIdentityBuilder.build_from_uuid(
                str(uuid.uuid4()),
            ),
            parcours_doctoral_id=parcours_doctoral_id,
            date_limite=date_limite,
        )
