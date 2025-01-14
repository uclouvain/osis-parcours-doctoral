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

from datetime import date
from typing import List, Optional, Tuple

from admission.views import PaginatedList
from parcours_doctoral.ddd.read_view.dto.parcours_doctoral import (
    ListeParcoursDoctoralRechercheDTO,
)
from parcours_doctoral.ddd.read_view.repository.i_liste_parcours_doctoraux import (
    IListeParcoursDoctorauxRepository,
)
from parcours_doctoral.infrastructure.parcours_doctoral.repository.in_memory.parcours_doctoral import (
    ParcoursDoctoralInMemoryRepository,
)


class ListeParcoursDoctorauxInMemoryRepository(IListeParcoursDoctorauxRepository):
    @classmethod
    def get(
        cls,
        numero: Optional[int] = None,
        noma: Optional[str] = '',
        matricule_doctorant: Optional[str] = '',
        type_admission: Optional[str] = '',
        annee_academique: Optional[int] = None,
        uuid_promoteur: Optional[str] = '',
        uuid_president_jury: Optional[str] = '',
        cdds: Optional[List[str]] = None,
        commission_proximite: Optional[str] = '',
        type_financement: Optional[str] = '',
        bourse_recherche: Optional[str] = '',
        fnrs_fria_fresh: Optional[bool] = None,
        instituts_secteurs: Optional[List[str]] = None,
        statuts: Optional[List] = None,
        dates: Optional[List[Tuple[str, Optional[date], Optional[date]]]] = None,
        sigles_formations: Optional[List[str]] = None,
        indicateur_tableau_bord: Optional[str] = '',
        tri_inverse: bool = False,
        champ_tri: Optional[str] = None,
        page: Optional[int] = None,
        taille_page: Optional[int] = None,
        demandeur: Optional[str] = '',
    ) -> ListeParcoursDoctoralRechercheDTO:

        result = PaginatedList(id_attribute='uuid')

        for parcours_doctoral in ParcoursDoctoralInMemoryRepository.search_dto(matricule_doctorant=matricule_doctorant):
            result.append(parcours_doctoral)

        return ListeParcoursDoctoralRechercheDTO(parcours_doctoraux=result)
