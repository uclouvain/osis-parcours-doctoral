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
import datetime

import attr

from base.ddd.utils.business_validator import BusinessValidator
from parcours_doctoral.ddd.defense_privee.validators.exceptions import (
    DefensePriveeNonActiveeException,
    DefensePriveeNonCompleteeException,
    StatutDoctoratDifferentDefensePriveeAutoriseeException,
    StatutDoctoratDifferentDefensePriveeSoumiseException,
)
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral


@attr.dataclass(frozen=True, slots=True)
class ShouldDefensePriveeEtreCompletee(BusinessValidator):
    titre_these: str
    date_heure: datetime.datetime

    def validate(self, *args, **kwargs):
        if not self.date_heure or not self.titre_these:
            raise DefensePriveeNonCompleteeException


@attr.dataclass(frozen=True, slots=True)
class ShouldDefensePriveeEtreActive(BusinessValidator):
    est_active: bool

    def validate(self, *args, **kwargs):
        if not self.est_active:
            raise DefensePriveeNonActiveeException


@attr.dataclass(frozen=True, slots=True)
class ShouldStatutDoctoratEtreDefensePriveeSoumise(BusinessValidator):
    statut: ChoixStatutParcoursDoctoral

    def validate(self, *args, **kwargs):
        if self.statut != ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE:
            raise StatutDoctoratDifferentDefensePriveeSoumiseException


@attr.dataclass(frozen=True, slots=True)
class ShouldStatutDoctoratEtreDefensePriveeAutorisee(BusinessValidator):
    statut: ChoixStatutParcoursDoctoral

    def validate(self, *args, **kwargs):
        if self.statut != ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_AUTORISEE:
            raise StatutDoctoratDifferentDefensePriveeAutoriseeException
