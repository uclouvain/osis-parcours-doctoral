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
from typing import Dict, List, Optional

from admission.ddd.admission.doctorat.preparation.read_view.domain.enums.tableau_bord import (
    IndicateurTableauBordEnum,
)
from parcours_doctoral.ddd.read_view.repository.i_tableau_bord import (
    ITableauBordRepository,
)


class TableauBordInMemoryRepository(ITableauBordRepository):
    @classmethod
    def _get_valeurs_indicateurs(
        cls,
        commission_proximite: Optional[str],
        cdds: Optional[List[str]],
    ) -> Dict[str, int]:
        return {indicator.name: 0 for indicator in IndicateurTableauBordEnum}
