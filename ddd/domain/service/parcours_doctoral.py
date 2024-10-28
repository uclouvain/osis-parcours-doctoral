# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import Proposition
from parcours_doctoral.ddd.domain.model._formation import FormationIdentity
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoral, ParcoursDoctoralIdentity
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from osis_common.ddd import interface


class ParcoursDoctoralService(interface.DomainService):
    @classmethod
    def initier(cls, proposition: 'Proposition') -> ParcoursDoctoral:
        entity_id = ParcoursDoctoralIdentity(uuid=proposition.entity_id.uuid)
        return ParcoursDoctoral(
            entity_id=entity_id,
            formation_id=FormationIdentity(sigle=proposition.sigle_formation, annee=proposition.annee),
            matricule_doctorant=proposition.matricule_candidat,
            reference=proposition.reference,
            statut=ChoixStatutParcoursDoctoral.ADMITTED,
        )