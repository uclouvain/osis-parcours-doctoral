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
import datetime

import attr

from admission.views import PaginatedList
from osis_common.ddd import interface
from parcours_doctoral.ddd.read_view.dto.formation import FormationRechercheDTO


@attr.dataclass(slots=True)
class ParcoursDoctoralRechercheDTO(interface.DTO):
    uuid: str
    reference: str
    statut: str
    type_admission: str

    formation: FormationRechercheDTO

    matricule_doctorant: str
    genre_doctorant: str
    prenom_doctorant: str
    nom_doctorant: str

    code_bourse: str
    cotutelle: bool
    formation_complementaire: bool
    en_regle_inscription: bool
    total_credits_valides: int

    cree_le: datetime.datetime
    date_admission_par_cdd: datetime.datetime


@attr.dataclass(slots=True)
class ListeParcoursDoctoralRechercheDTO(interface.DTO):
    parcours_doctoraux: PaginatedList[ParcoursDoctoralRechercheDTO]
