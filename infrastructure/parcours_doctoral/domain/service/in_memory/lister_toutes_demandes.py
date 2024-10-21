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
from typing import List, Optional

from admission.views import PaginatedList

from parcours_doctoral.ddd.domain.service.i_filtrer_tous_parcours_doctoraux import (
    IListerTousParcoursDoctoraux,
)
from parcours_doctoral.ddd.dtos import ParcoursDoctoralRechercheDTO
from parcours_doctoral.infrastructure.parcours_doctoral.repository.in_memory.parcours_doctoral import (
    ParcoursDoctoralInMemoryRepository,
)


class ListerTousParcoursDoctorauxInMemory(IListerTousParcoursDoctoraux):
    @classmethod
    def filtrer(
        cls,
        numero: Optional[int] = None,
        noma: Optional[str] = '',
        matricule_etudiant: Optional[str] = '',
        etats: Optional[List[str]] = None,
        formation: Optional[str] = '',
        tri_inverse: bool = False,
        champ_tri: Optional[str] = None,
        page: Optional[int] = None,
        taille_page: Optional[int] = None,
    ) -> PaginatedList[ParcoursDoctoralRechercheDTO]:

        result = PaginatedList(id_attribute='uuid')

        for parcours_doctoral in ParcoursDoctoralInMemoryRepository.search_dto(matricule_etudiant=matricule_etudiant):
            result.append(parcours_doctoral)

        return result
