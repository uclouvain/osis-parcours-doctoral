##############################################################################
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
##############################################################################
import uuid
from typing import Optional

import attr
from base.models.campus import Campus
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class CampusDTO(interface.DTO):
    uuid: uuid.UUID
    nom: str
    code_postal: str
    ville: str
    pays_iso_code: str
    nom_pays: str
    rue: str
    numero_rue: str
    boite_postale: str
    localisation: str

    def __str__(self):
        return self.nom

    @classmethod
    def from_model_object(cls, campus: Optional[Campus]):
        return (
            cls(
                uuid=campus.uuid,
                nom=campus.name,
                code_postal=campus.postal_code,
                ville=campus.city,
                pays_iso_code=campus.country.iso_code if campus.country_id else '',
                nom_pays=campus.country.name if campus.country_id else '',
                rue=campus.street,
                numero_rue=campus.street_number,
                boite_postale=campus.postal_box,
                localisation=campus.location,
            )
            if campus
            else None
        )
