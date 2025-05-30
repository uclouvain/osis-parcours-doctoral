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
from osis_common.ddd import interface

from parcours_doctoral.ddd.formation.domain.model.activite import Activite
from parcours_doctoral.ddd.formation.domain.model.enums import (
    CategorieActivite,
    StatutActivite,
)
from parcours_doctoral.ddd.formation.domain.validator.exceptions import (
    ActiviteDejaSoumise,
)
from parcours_doctoral.ddd.formation.repository.i_activite import IActiviteRepository


class SupprimerActivite(interface.DomainService):
    @classmethod
    def supprimer_activite(cls, activite: Activite, activite_repository: IActiviteRepository):
        if activite.statut != StatutActivite.NON_SOUMISE:
            raise ActiviteDejaSoumise(activite_id=activite.entity_id)

        sous_activites = []
        if activite.categorie in [CategorieActivite.CONFERENCE, CategorieActivite.RESIDENCY, CategorieActivite.SEMINAR]:
            sous_activites = activite_repository.search(parent_id=activite.entity_id)
            for sous_activite in sous_activites:
                if sous_activite.statut != StatutActivite.NON_SOUMISE:
                    raise ActiviteDejaSoumise(activite_id=sous_activite.entity_id)

        for sous_activite in sous_activites:
            activite_repository.delete(sous_activite.entity_id)
        activite_repository.delete(activite.entity_id)
