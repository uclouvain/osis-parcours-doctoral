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

import attr
from base.ddd.utils.business_validator import BusinessValidator

from parcours_doctoral.ddd.formation.business_types import *
from parcours_doctoral.ddd.formation.domain.validator.exceptions import (
    ActiviteNonComplete,
)
from parcours_doctoral.ddd.formation.dtos import PublicationDTO


@attr.dataclass(frozen=True, slots=True)
class ShouldPublicationEtreComplete(BusinessValidator):
    publication: 'PublicationDTO'
    activite: 'Activite'

    def validate(self, *args, **kwargs):
        if not all(
            [
                self.publication.type,
                self.publication.intitule,
                self.publication.date,
                self.publication.auteurs,
                self.publication.role,
                self.publication.nom_revue_maison_edition,
                self.publication.statut_publication,
                self.activite.ects,
                self.publication.preuve_acceptation,
            ]
        ):
            raise ActiviteNonComplete(activite_id=self.activite.entity_id)
