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
from typing import List

import attr

from base.ddd.utils.business_validator import (
    BusinessValidator,
    TwoStepsMultipleBusinessExceptionListValidator,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.enums import (
    ChoixStatutAutorisationDiffusionThese,
    TypeModalitesDiffusionThese,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.validator import *


@attr.dataclass(frozen=True, slots=True)
class AutorisationDiffusionTheseValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    sources_financement: str
    resume_anglais: str
    langue_redaction_these: str
    mots_cles: list[str]
    type_modalites_diffusion: TypeModalitesDiffusionThese | None
    date_embargo: datetime.date | None
    modalites_diffusion_acceptees: str
    modalites_diffusion_acceptees_le: datetime.date | None
    statut: ChoixStatutAutorisationDiffusionThese

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldSourcesFinancementEtreCompletees(
                sources_financement=self.sources_financement,
            ),
            ShouldResumeAnglaisEtreCompletee(
                resume_anglais=self.resume_anglais,
            ),
            ShouldLangueRedactionTheseEtreCompletee(
                langue_redaction_these=self.langue_redaction_these,
            ),
            ShouldMotsClesEtreCompletes(
                mots_cles=self.mots_cles,
            ),
            ShouldTypeModalitesDiffusionEtreCompletee(
                type_modalites_diffusion=self.type_modalites_diffusion,
            ),
            ShouldDateEmbargoModalitesDiffusionEtreCompletee(
                type_modalites_diffusion=self.type_modalites_diffusion,
                date_embargo=self.date_embargo,
            ),
            ShouldModalitesDiffusionEtreAcceptees(
                modalites_diffusion_acceptees=self.modalites_diffusion_acceptees,
                modalites_diffusion_acceptees_le=self.modalites_diffusion_acceptees_le,
            ),
            ShouldAutorisationDiffusionTheseEtreModifiable(
                statut=self.statut,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class ModifierAutorisationDiffusionTheseValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    statut: ChoixStatutAutorisationDiffusionThese

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldAutorisationDiffusionTheseEtreModifiable(
                statut=self.statut,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class RefuserTheseParPromoteurValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    statut: ChoixStatutAutorisationDiffusionThese
    motifs_refus: str
    signataire: 'SignataireAutorisationDiffusionThese'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldStatutAutorisationDiffusionTheseEtreSoumis(
                statut=self.statut,
            ),
            ShouldSignataireEtrePromoteur(
                signataire=self.signataire,
            ),
            ShouldSignataireEtreInvite(
                signataire=self.signataire,
            ),
            ShouldMotifRefusEtreSpecifie(
                motifs_refus=self.motifs_refus,
            ),
        ]
