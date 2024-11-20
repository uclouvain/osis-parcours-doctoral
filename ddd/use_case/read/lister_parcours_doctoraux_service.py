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

from typing import List

from parcours_doctoral.ddd.commands import ListerTousParcoursDoctorauxQuery
from parcours_doctoral.ddd.dtos import ParcoursDoctoralDTO


def lister_demandes(
    cmd: 'ListerTousParcoursDoctorauxQuery',
    lister_tous_parcours_doctoraux_service: 'IListerTousParcoursDoctoraux',
) -> 'List[ParcoursDoctoralDTO]':
    return lister_tous_parcours_doctoraux_service.filtrer(
        numero=cmd.numero,
        noma=cmd.noma,
        matricule_etudiant=cmd.matricule_etudiant,
        etats=cmd.etats,
        formation=cmd.formation,
        tri_inverse=cmd.tri_inverse,
        champ_tri=cmd.champ_tri,
        page=cmd.page,
        taille_page=cmd.taille_page,
    )
