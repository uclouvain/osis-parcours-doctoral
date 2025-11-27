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
from typing import Optional

import attr

from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class SoumettreDefensePriveeEtSoutenancePubliqueCommand(interface.CommandRequest):
    uuid_parcours_doctoral: str
    matricule_auteur: str

    titre_these: str
    langue_soutenance_publique: str

    date_heure_defense_privee: datetime.datetime
    lieu_defense_privee: Optional[str]
    date_envoi_manuscrit: Optional[datetime.date]

    date_heure_soutenance_publique: datetime.datetime
    lieu_soutenance_publique: Optional[str]
    local_deliberation: Optional[str]
    resume_annonce: Optional[str]
    photo_annonce: list[str]
