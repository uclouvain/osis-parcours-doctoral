# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from base.ddd.utils.business_validator import BusinessValidator, TwoStepsMultipleBusinessExceptionListValidator
from parcours_doctoral.ddd.domain.model._cotutelle import Cotutelle
from parcours_doctoral.ddd.domain.model._institut import InstitutIdentity
from parcours_doctoral.ddd.domain.model._membre_CA import MembreCAIdentity
from parcours_doctoral.ddd.domain.model._projet import Projet
from parcours_doctoral.ddd.domain.model._promoteur import PromoteurIdentity
from parcours_doctoral.ddd.domain.model._signature_promoteur import SignaturePromoteur
from parcours_doctoral.ddd.domain.model.enums import ChoixDoctoratDejaRealise
from parcours_doctoral.ddd.domain.validator import *


@attr.dataclass(frozen=True, slots=True)
class IdentifierPromoteurValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision: 'GroupeDeSupervision'
    matricule: Optional[str]
    prenom: Optional[str]
    nom: Optional[str]
    email: Optional[str]
    institution: Optional[str]
    ville: Optional[str]
    pays: Optional[str]
    langue: Optional[str]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldGroupeDeSupervisionNonCompletPourPromoteurs(self.groupe_de_supervision),
            ShouldMembreEtreInterneOuExterne(
                self.matricule,
                self.prenom,
                self.nom,
                self.email,
                self.institution,
                self.ville,
                self.pays,
                self.langue,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class IdentifierMembreCAValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision: 'GroupeDeSupervision'
    matricule: Optional[str]
    prenom: Optional[str]
    nom: Optional[str]
    email: Optional[str]
    institution: Optional[str]
    ville: Optional[str]
    pays: Optional[str]
    langue: Optional[str]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldGroupeDeSupervisionNonCompletPourMembresCA(self.groupe_de_supervision),
            ShouldMembreEtreInterneOuExterne(
                self.matricule,
                self.prenom,
                self.nom,
                self.email,
                self.institution,
                self.ville,
                self.pays,
                self.langue,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class DesignerPromoteurReferenceValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision: 'GroupeDeSupervision'
    promoteur_id: 'PromoteurIdentity'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldPromoteurEtreDansGroupeDeSupervision(self.groupe_de_supervision, self.promoteur_id),
        ]


@attr.dataclass(frozen=True, slots=True)
class SupprimerPromoteurValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision: 'GroupeDeSupervision'
    promoteur_id: 'PromoteurIdentity'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldPromoteurEtreDansGroupeDeSupervision(self.groupe_de_supervision, self.promoteur_id),
        ]


@attr.dataclass(frozen=True, slots=True)
class SupprimerMembreCAValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision: 'GroupeDeSupervision'
    membre_CA_id: 'MembreCAIdentity'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldMembreCAEtreDansGroupeDeSupervision(self.groupe_de_supervision, self.membre_CA_id),
        ]


@attr.dataclass(frozen=True, slots=True)
class InviterASignerValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision: 'GroupeDeSupervision'
    signataire_id: Union['PromoteurIdentity', 'MembreCAIdentity']

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldSignataireEtreDansGroupeDeSupervision(self.groupe_de_supervision, self.signataire_id),
            ShouldSignatairePasDejaInvite(self.groupe_de_supervision, self.signataire_id),
        ]


@attr.dataclass(frozen=True, slots=True)
class ApprouverValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision: 'GroupeDeSupervision'
    signataire_id: Union['PromoteurIdentity', 'MembreCAIdentity']

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldSignataireEtreDansGroupeDeSupervision(self.groupe_de_supervision, self.signataire_id),
            ShouldSignataireEtreInvite(self.groupe_de_supervision, self.signataire_id),
        ]


@attr.dataclass(frozen=True, slots=True)
class CotutelleValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    cotutelle: Optional['Cotutelle']

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldCotutelleEtreComplete(self.cotutelle),
        ]


@attr.dataclass(frozen=True, slots=True)
class SignatairesValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision: 'GroupeDeSupervision'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldGroupeDeSupervisionAvoirAuMoinsDeuxMembreCA(self.groupe_de_supervision.signatures_membres_CA),
            ShouldGroupeDeSupervisionAvoirUnPromoteurDeReference(self.groupe_de_supervision),
        ]


@attr.dataclass(frozen=True, slots=True)
class ApprobationValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    groupe_de_supervision: 'GroupeDeSupervision'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldDemandeSignatureLancee(self.groupe_de_supervision.statut_signature),
            ShouldPromoteursOntApprouve(self.groupe_de_supervision.signatures_promoteurs),
            ShouldMembresCAOntApprouve(self.groupe_de_supervision.signatures_membres_CA),
        ]


@attr.dataclass(frozen=True, slots=True)
class ApprobationPromoteurValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    signatures_promoteurs: List['SignaturePromoteur']
    signataire: Union['PromoteurIdentity', 'MembreCAIdentity']
    promoteur_reference: Optional[PromoteurIdentity]
    proposition_institut_these: Optional[InstitutIdentity]
    institut_these: Optional[str]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldPromoteurReferenceRenseignerInstitutThese(
                self.signatures_promoteurs,
                self.signataire,
                self.promoteur_reference,
                self.proposition_institut_these,
                self.institut_these,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class ProjetDoctoralValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    projet: 'Projet'
    financement: 'Financement'
    experience_precedente_recherche: 'ExperiencePrecedenteRecherche'
    cotutelle: 'Cotutelle'

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldProjetEtreComplet(
                self.projet,
                self.financement,
                self.experience_precedente_recherche,
            ),
            ShouldCotutelleEtreComplete(self.cotutelle),
        ]


@attr.dataclass(frozen=True, slots=True)
class ModifierProjetValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    type_financement: Optional[str] = ''
    type_contrat_travail: Optional[str] = ''
    doctorat_deja_realise: str = ChoixDoctoratDejaRealise.NO.name
    institution: Optional[str] = ''
    domaine_these: Optional[str] = ''

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldTypeContratTravailDependreTypeFinancement(self.type_financement, self.type_contrat_travail),
            ShouldInstitutionDependreDoctoratRealise(self.doctorat_deja_realise, self.institution),
            ShouldDomaineDependreDoctoratRealise(self.doctorat_deja_realise, self.domaine_these),
        ]


@attr.dataclass(frozen=True, slots=True)
class ModifierFinancementValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    type: Optional[str] = ''
    type_contrat_travail: Optional[str] = ''

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldTypeContratTravailDependreTypeFinancement(self.type, self.type_contrat_travail),
        ]
