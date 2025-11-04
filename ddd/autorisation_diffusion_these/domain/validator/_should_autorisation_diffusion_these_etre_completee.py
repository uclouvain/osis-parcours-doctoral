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
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.enums import (
    TypeModalitesDiffusionThese,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.validator.exceptions import (
    DateEmbargoModalitesDiffusionNonCompleteeException,
    LangueRedactionTheseNonCompleteeException,
    ModalitesDiffusionNonAccepteesException,
    MotsClesNonCompletesException,
    ResumeAnglaisNonCompleteException,
    SourcesFinancementsNonCompleteesException,
    TypeModalitesDiffusionNonCompleteException,
)

__all__ = [
    'ShouldSourcesFinancementEtreCompletees',
    'ShouldResumeAnglaisEtreCompletee',
    'ShouldLangueRedactionTheseEtreCompletee',
    'ShouldMotsClesEtreCompletes',
    'ShouldTypeModalitesDiffusionEtreCompletee',
    'ShouldDateEmbargoModalitesDiffusionEtreCompletee',
    'ShouldModalitesDiffusionEtreAcceptees',
]


@attr.dataclass(frozen=True, slots=True)
class ShouldSourcesFinancementEtreCompletees(BusinessValidator):
    sources_financement: str

    def validate(self, *args, **kwargs):
        if not self.sources_financement:
            raise SourcesFinancementsNonCompleteesException


@attr.dataclass(frozen=True, slots=True)
class ShouldResumeAnglaisEtreCompletee(BusinessValidator):
    resume_anglais: str

    def validate(self, *args, **kwargs):
        if not self.resume_anglais:
            raise ResumeAnglaisNonCompleteException


@attr.dataclass(frozen=True, slots=True)
class ShouldLangueRedactionTheseEtreCompletee(BusinessValidator):
    langue_redaction_these: str

    def validate(self, *args, **kwargs):
        if not self.langue_redaction_these:
            raise LangueRedactionTheseNonCompleteeException


@attr.dataclass(frozen=True, slots=True)
class ShouldMotsClesEtreCompletes(BusinessValidator):
    mots_cles: list[str]

    def validate(self, *args, **kwargs):
        if not self.mots_cles:
            raise MotsClesNonCompletesException


@attr.dataclass(frozen=True, slots=True)
class ShouldTypeModalitesDiffusionEtreCompletee(BusinessValidator):
    type_modalites_diffusion: TypeModalitesDiffusionThese | None

    def validate(self, *args, **kwargs):
        if not self.type_modalites_diffusion:
            raise TypeModalitesDiffusionNonCompleteException


@attr.dataclass(frozen=True, slots=True)
class ShouldDateEmbargoModalitesDiffusionEtreCompletee(BusinessValidator):
    type_modalites_diffusion: TypeModalitesDiffusionThese | None
    date_embargo: datetime.date | None

    def validate(self, *args, **kwargs):
        if self.type_modalites_diffusion == TypeModalitesDiffusionThese.ACCES_EMBARGO and not self.date_embargo:
            raise DateEmbargoModalitesDiffusionNonCompleteeException


@attr.dataclass(frozen=True, slots=True)
class ShouldModalitesDiffusionEtreAcceptees(BusinessValidator):
    modalites_diffusion_acceptees: str
    modalites_diffusion_acceptees_le: datetime.date | None

    def validate(self, *args, **kwargs):
        if not self.modalites_diffusion_acceptees or not self.modalites_diffusion_acceptees_le:
            raise ModalitesDiffusionNonAccepteesException
