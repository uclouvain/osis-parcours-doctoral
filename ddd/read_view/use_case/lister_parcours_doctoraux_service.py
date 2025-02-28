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

from admission.views import PaginatedList
from parcours_doctoral.ddd.read_view.dto.parcours_doctoral import (
    ParcoursDoctoralRechercheDTO,
)
from parcours_doctoral.ddd.read_view.queries import ListerTousParcoursDoctorauxQuery
from parcours_doctoral.ddd.read_view.repository.i_liste_parcours_doctoraux import (
    IListeParcoursDoctorauxRepository,
)


def lister_parcours_doctoraux(
    cmd: 'ListerTousParcoursDoctorauxQuery',
    lister_tous_parcours_doctoraux_service: 'IListeParcoursDoctorauxRepository',
) -> 'PaginatedList[ParcoursDoctoralRechercheDTO]':
    return lister_tous_parcours_doctoraux_service.get(
        numero=cmd.numero,
        noma=cmd.noma,
        matricule_doctorant=cmd.matricule_doctorant,
        type_admission=cmd.type_admission,
        annee_academique=cmd.annee_academique,
        uuid_promoteur=cmd.uuid_promoteur,
        uuid_president_jury=cmd.uuid_president_jury,
        cdds=cmd.cdds,
        commission_proximite=cmd.commission_proximite,
        type_financement=cmd.type_financement,
        bourse_recherche=cmd.bourse_recherche,
        fnrs_fria_fresh=cmd.fnrs_fria_fresh,
        instituts=cmd.instituts,
        secteurs=cmd.secteurs,
        statuts=cmd.statuts,
        dates=cmd.dates,
        sigles_formations=cmd.sigles_formations,
        indicateur_tableau_bord=cmd.indicateur_tableau_bord,
        tri_inverse=cmd.tri_inverse,
        champ_tri=cmd.champ_tri,
        page=cmd.page,
        taille_page=cmd.taille_page,
        demandeur=cmd.demandeur,
    ).parcours_doctoraux
