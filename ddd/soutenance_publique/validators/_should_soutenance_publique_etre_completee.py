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

import attr

from base.ddd.utils.business_validator import BusinessValidator
from parcours_doctoral.ddd.domain.model.enums import ChoixLangueDefense
from parcours_doctoral.ddd.soutenance_publique.validators.exceptions import (
    SoutenancePubliqueNonCompleteeException,
)


@attr.dataclass(frozen=True, slots=True)
class ShouldSoutenancePubliqueEtreCompletee(BusinessValidator):
    langue_soutenance_publique: str
    autre_langue_soutenance_publique: str
    date_heure_soutenance_publique: Optional[datetime.datetime]
    photo_annonce: list[str]

    def validate(self, *args, **kwargs):
        if (
            not self.langue_soutenance_publique
            or not self.date_heure_soutenance_publique
            or not self.photo_annonce
            or (
                self.langue_soutenance_publique == ChoixLangueDefense.OTHER.name
                and not self.autre_langue_soutenance_publique
            )
        ):
            raise SoutenancePubliqueNonCompleteeException
