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

from datetime import date
from typing import List, Optional

import attr

from osis_common.ddd import interface


@attr.dataclass(slots=True, frozen=True)
class SeminaireDTO(interface.DTO):
    type: str = ""
    nom: str = ""
    pays: str = ""
    ville: str = ""
    institution_organisatrice: str = ""
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    volume_horaire: str = ""
    volume_horaire_type: str = ""
    attestation_participation: List[str] = attr.Factory(list)


@attr.dataclass(slots=True, frozen=True)
class SeminaireCommunicationDTO(interface.DTO):
    date: Optional[date] = None
    en_ligne: bool = False
    site_web: str = ""
    titre_communication: str = ""
    orateur_oratrice: str = ""
    commentaire: str = ""
    attestation_participation: List[str] = attr.Factory(list)
