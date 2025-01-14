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
from typing import List, Optional, Tuple

import attr

from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class ListerTousParcoursDoctorauxQuery(interface.QueryRequest):
    tri_inverse: bool = False
    champ_tri: Optional[str] = None
    page: Optional[int] = None
    taille_page: Optional[int] = None

    annee_academique: Optional[int] = None
    type_admission: Optional[str] = ''
    numero: Optional[int] = None
    noma: Optional[str] = ''
    matricule_doctorant: Optional[str] = ''
    uuid_promoteur: Optional[str] = ''
    uuid_president_jury: Optional[str] = ''
    sigles_formations: Optional[List[str]] = None
    cdds: Optional[List[str]] = None
    commission_proximite: Optional[str] = ''
    type_financement: Optional[str] = ''
    bourse_recherche: Optional[str] = ''
    fnrs_fria_fresh: Optional[bool] = None
    instituts_secteurs: Optional[List[str]] = None
    statuts: Optional[List] = None
    indicateur_tableau_bord: Optional[str] = ''
    dates: Optional[List[Tuple[str, Optional[datetime.date], Optional[datetime.date]]]] = None
    demandeur: Optional[str] = ''


@attr.dataclass(frozen=True, slots=True)
class RecupererInformationsTableauBordQuery(interface.QueryRequest):
    pass
