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
from typing import List, Optional, Union

import attr

from base.ddd.utils.business_validator import (
    BusinessValidator,
    TwoStepsMultipleBusinessExceptionListValidator,
)
from parcours_doctoral.ddd.jury.domain.validator._should_jury_avoir_assez_de_membres import (
    ShouldJuryAvoirAssezDeMembres,
)
from parcours_doctoral.ddd.jury.domain.validator._should_jury_avoir_un_membre_externe import (
    ShouldJuryAvoirUnMembreExterne,
)
from parcours_doctoral.ddd.jury.domain.validator._should_matricule_ne_pas_etre_dans_jury import (
    ShouldMatriculeNePasEtreDansJuryValidator,
)
from parcours_doctoral.ddd.jury.domain.validator._should_membre_etre_dans_jury import (
    ShouldMembreEtreDansJuryValidator,
)
from parcours_doctoral.ddd.jury.domain.validator._should_membre_externe_avoir_email import (
    ShouldMembreExterneAvoirEmail,
)
from parcours_doctoral.ddd.jury.domain.validator._should_membre_externe_avoir_genre import (
    ShouldMembreExterneAvoirGenre,
)
from parcours_doctoral.ddd.jury.domain.validator._should_membre_externe_avoir_institution import (
    ShouldMembreExterneAvoirInstitution,
)
from parcours_doctoral.ddd.jury.domain.validator._should_membre_externe_avoir_langue_de_contact import (
    ShouldMembreExterneAvoirLangueDeContact,
)
from parcours_doctoral.ddd.jury.domain.validator._should_membre_externe_avoir_nom import (
    ShouldMembreExterneAvoirNom,
)
from parcours_doctoral.ddd.jury.domain.validator._should_membre_externe_avoir_pays import (
    ShouldMembreExterneAvoirPays,
)
from parcours_doctoral.ddd.jury.domain.validator._should_membre_externe_avoir_prenom import (
    ShouldMembreExterneAvoirPrenom,
)
from parcours_doctoral.ddd.jury.domain.validator._should_membre_externe_avoir_titre import (
    ShouldMembreExterneAvoirTitre,
)
from parcours_doctoral.ddd.jury.domain.validator._should_methode_de_defense_etre_complete import (
    ShouldMethodeDeDefenseEtreCompletee,
)
from parcours_doctoral.ddd.jury.domain.validator._should_non_docteur_avoir_justification import (
    ShouldNonDocteurAvoirJustification,
)
from parcours_doctoral.ddd.jury.domain.validator._should_signataire_etre_dans_jury import (
    ShouldSignataireEtreDansJury,
)
from parcours_doctoral.ddd.jury.domain.validator._should_signataire_etre_invite import (
    ShouldSignataireEtreInvite,
)
from parcours_doctoral.ddd.jury.domain.validator._should_signataire_pas_invite import (
    ShouldSignatairePasDejaInvite,
)


@attr.dataclass(frozen=True, slots=True)
class VerifierJuryConditionSignature(TwoStepsMultipleBusinessExceptionListValidator):
    jury: 'Jury'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldJuryAvoirAssezDeMembres(self.jury),
            ShouldJuryAvoirUnMembreExterne(self.jury),
            ShouldMethodeDeDefenseEtreCompletee(self.jury),
        ]


@attr.dataclass(frozen=True, slots=True)
class InviterASignerValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    jury: 'Jury'
    signataire_id: str

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldSignataireEtreDansJury(self.jury, self.signataire_id),
            ShouldSignatairePasDejaInvite(self.jury, self.signataire_id),
        ]


@attr.dataclass(frozen=True, slots=True)
class ApprouverValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    jury: 'Jury'
    signataire_id: str

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldSignataireEtreDansJury(self.jury, self.signataire_id),
            ShouldSignataireEtreInvite(self.jury, self.signataire_id),
        ]


@attr.dataclass(frozen=True, slots=True)
class JuryValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    jury: 'Jury'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return []


@attr.dataclass(frozen=True, slots=True)
class AjouterMembreValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    jury: 'Jury'
    membre: 'MembreJury'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldMatriculeNePasEtreDansJuryValidator(self.membre.matricule, self.jury),
            ShouldNonDocteurAvoirJustification(self.membre),
            ShouldMembreExterneAvoirInstitution(self.membre),
            ShouldMembreExterneAvoirPays(self.membre),
            ShouldMembreExterneAvoirNom(self.membre),
            ShouldMembreExterneAvoirPrenom(self.membre),
            ShouldMembreExterneAvoirTitre(self.membre),
            ShouldMembreExterneAvoirGenre(self.membre),
            ShouldMembreExterneAvoirEmail(self.membre),
            ShouldMembreExterneAvoirLangueDeContact(self.membre),
        ]


@attr.dataclass(frozen=True, slots=True)
class RecupererMembreValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    jury: 'Jury'
    uuid_membre: str

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [ShouldMembreEtreDansJuryValidator(self.uuid_membre, self.jury)]


@attr.dataclass(frozen=True, slots=True)
class ModifierMembreValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    jury: 'Jury'
    membre: 'MembreJury'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldMembreEtreDansJuryValidator(self.membre.uuid, self.jury),
            ShouldNonDocteurAvoirJustification(self.membre),
            ShouldMembreExterneAvoirInstitution(self.membre),
            ShouldMembreExterneAvoirPays(self.membre),
            ShouldMembreExterneAvoirNom(self.membre),
            ShouldMembreExterneAvoirPrenom(self.membre),
            ShouldMembreExterneAvoirTitre(self.membre),
            ShouldMembreExterneAvoirGenre(self.membre),
            ShouldMembreExterneAvoirEmail(self.membre),
            ShouldMembreExterneAvoirLangueDeContact(self.membre),
        ]


@attr.dataclass(frozen=True, slots=True)
class RetirerMembreValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    jury: 'Jury'
    uuid_membre: str

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [ShouldMembreEtreDansJuryValidator(self.uuid_membre, self.jury)]


@attr.dataclass(frozen=True, slots=True)
class ModifierRoleMembreValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    jury: 'Jury'
    uuid_membre: str

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [ShouldMembreEtreDansJuryValidator(self.uuid_membre, self.jury)]
