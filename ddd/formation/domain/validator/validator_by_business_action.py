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

import attr
from base.ddd.utils.business_validator import (
    BusinessValidator,
    TwoStepsMultipleBusinessExceptionListValidator,
)

from parcours_doctoral.ddd.formation.business_types import *
from parcours_doctoral.ddd.formation.domain.validator import *
from parcours_doctoral.ddd.formation.domain.validator._should_ects_etre_positif import (
    ShouldEctsEtrePositif,
)
from parcours_doctoral.ddd.formation.dtos import *

__all__ = [
    "ConferenceValidatorList",
    "ConferenceCommunicationValidatorList",
    "CommunicationValidatorList",
    "ConferencePublicationValidatorList",
    "PublicationValidatorList",
    "SejourValidatorList",
    "SejourCommunicationValidatorList",
    "SeminaireValidatorList",
    "SeminaireCommunicationValidatorList",
    "ServiceValidatorList",
    "ValorisationValidatorList",
    "CoursValidatorList",
    "EpreuveValidatorList",
    "RefusActiviteValidationList",
    "RevenirASoumiseActiviteValidationList",
]


@attr.dataclass(frozen=True, slots=True)
class ConferenceValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    conference: 'ConferenceDTO'
    activite: 'Activite'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [ShouldConferenceEtreComplete(self.conference, self.activite), ShouldEctsEtrePositif(self.activite.ects)]


@attr.dataclass(frozen=True, slots=True)
class ConferenceCommunicationValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    communication: 'ConferenceCommunicationDTO'
    activite: 'Activite'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldCommunicationConferenceEtreComplete(self.communication, self.activite),
            ShouldEctsEtrePositif(self.activite.ects),
        ]


@attr.dataclass(frozen=True, slots=True)
class CommunicationValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    communication: 'CommunicationDTO'
    activite: 'Activite'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldCommunicationEtreComplete(self.communication, self.activite),
            ShouldEctsEtrePositif(self.activite.ects),
        ]


@attr.dataclass(frozen=True, slots=True)
class ConferencePublicationValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    publication: 'ConferencePublicationDTO'
    activite: 'Activite'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldPublicationConferenceEtreComplete(self.publication, self.activite),
            ShouldEctsEtrePositif(self.activite.ects),
        ]


@attr.dataclass(frozen=True, slots=True)
class PublicationValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    publication: 'PublicationDTO'
    activite: 'Activite'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldPublicationEtreComplete(self.publication, self.activite),
            ShouldEctsEtrePositif(self.activite.ects),
        ]


@attr.dataclass(frozen=True, slots=True)
class SejourValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    sejour: 'SejourDTO'
    activite: 'Activite'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [ShouldSejourEtreComplet(self.sejour, self.activite), ShouldEctsEtrePositif(self.activite.ects)]


@attr.dataclass(frozen=True, slots=True)
class SejourCommunicationValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    communication: 'SejourCommunicationDTO'
    activite: 'Activite'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldCommunicationSejourEtreComplete(self.communication, self.activite),
            ShouldEctsEtrePositif(self.activite.ects),
        ]


@attr.dataclass(frozen=True, slots=True)
class SeminaireValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    seminaire: 'SeminaireDTO'
    activite: 'Activite'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [ShouldSeminaireEtreComplet(self.seminaire, self.activite), ShouldEctsEtrePositif(self.activite.ects)]


@attr.dataclass(frozen=True, slots=True)
class SeminaireCommunicationValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    communication: 'SeminaireCommunicationDTO'
    activite: 'Activite'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldCommunicationSeminaireEtreComplete(self.communication, self.activite),
            ShouldEctsEtrePositif(self.activite.ects),
        ]


@attr.dataclass(frozen=True, slots=True)
class ServiceValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    service: 'ServiceDTO'
    activite: 'Activite'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [ShouldServiceEtreComplet(self.service, self.activite), ShouldEctsEtrePositif(self.activite.ects)]


@attr.dataclass(frozen=True, slots=True)
class ValorisationValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    valorisation: 'ValorisationDTO'
    activite: 'Activite'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldValorisationEtreComplete(self.valorisation, self.activite),
            ShouldEctsEtrePositif(self.activite.ects),
        ]


@attr.dataclass(frozen=True, slots=True)
class CoursValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    cours: 'CoursDTO'
    activite: 'Activite'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [ShouldCoursEtreComplet(self.cours, self.activite), ShouldEctsEtrePositif(self.activite.ects)]


@attr.dataclass(frozen=True, slots=True)
class EpreuveValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    epreuve: 'EpreuveDTO'
    activite: 'Activite'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [ShouldEpreuveEtreComplete(self.epreuve, self.activite), ShouldEctsEtrePositif(self.activite.ects)]


@attr.dataclass(frozen=True, slots=True)
class RefusActiviteValidationList(TwoStepsMultipleBusinessExceptionListValidator):
    activite: 'Activite'
    remarque: str

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldActiviteEtreSoumise(self.activite),
            ShouldRemarqueEtrePresente(self.remarque),
        ]


@attr.dataclass(frozen=True, slots=True)
class RevenirASoumiseActiviteValidationList(TwoStepsMultipleBusinessExceptionListValidator):
    activite: 'Activite'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldActiviteEtreAccepteeOuRefusee(self.activite),
        ]
