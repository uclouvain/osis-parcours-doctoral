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
import uuid
from typing import List, Optional

import attr

from osis_common.ddd import interface
from parcours_doctoral.ddd.jury.domain.model.enums import (
    ChoixEtatSignature,
    ChoixStatutSignature,
    GenreMembre,
    RoleJury,
    TitreMembre,
)
from parcours_doctoral.ddd.jury.domain.validator.exceptions import (
    PasUnMembreException,
    PromoteurModifieException,
    PromoteurPresidentException,
    PromoteurRetireException,
    SignataireNonTrouveException,
)
from parcours_doctoral.ddd.jury.domain.validator.validator_by_business_action import (
    AjouterMembreValidatorList,
    ApprouverValidatorList,
    InviterASignerValidatorList,
    JuryValidatorList,
    ModifierMembreValidatorList,
    ModifierRoleMembreValidatorList,
    RecupererMembreValidatorList,
    RetirerMembreValidatorList,
)


@attr.dataclass(frozen=True, slots=True, eq=True, hash=True)
class SignatureMembre(interface.ValueObject):
    etat: ChoixEtatSignature = ChoixEtatSignature.NOT_INVITED
    date: Optional[datetime.datetime] = None
    commentaire_externe: str = ''
    commentaire_interne: str = ''
    motif_refus: str = ''
    pdf: List[str] = attr.Factory(list)


@attr.dataclass(frozen=True, slots=True, eq=True, hash=True)
class MembreJury(interface.ValueObject):
    est_promoteur: bool
    est_promoteur_de_reference: bool
    matricule: Optional[str]
    institution: str
    autre_institution: Optional[str]
    pays: str
    nom: str
    prenom: str
    titre: Optional['TitreMembre']
    justification_non_docteur: Optional[str]
    genre: Optional['GenreMembre']
    langue: str
    email: str
    signature: SignatureMembre = attr.Factory(SignatureMembre)
    uuid: str = attr.Factory(uuid.uuid4)
    role: 'RoleJury' = RoleJury.MEMBRE


@attr.dataclass(frozen=True, slots=True)
class MembreJuryIdentity(interface.EntityIdentity):
    uuid: str


@attr.dataclass(frozen=True, slots=True)
class JuryIdentity(interface.EntityIdentity):
    uuid: str


@attr.dataclass(slots=True, hash=False, eq=False)
class Jury(interface.RootEntity):
    entity_id: 'JuryIdentity'
    titre_propose: str
    formule_defense: str
    date_indicative: str
    langue_redaction: str
    langue_soutenance: str
    commentaire: str
    situation_comptable: Optional[bool] = None
    approbation_pdf: List[str] = attr.Factory(list)
    statut_signature: ChoixStatutSignature = ChoixStatutSignature.IN_PROGRESS

    membres: List[MembreJury] = attr.Factory(list)

    def _supprimer_membres_role(self, role: 'RoleJury'):
        self.membres = [membre for membre in self.membres if membre.role != role]

    def validate(self):
        JuryValidatorList(self).validate()

    def modifier(
        self, titre_propose, formule_defense, date_indicative, langue_redaction, langue_soutenance, commentaire
    ):
        self.titre_propose = titre_propose
        self.formule_defense = formule_defense
        self.date_indicative = date_indicative
        self.langue_redaction = langue_redaction
        self.langue_soutenance = langue_soutenance
        self.commentaire = commentaire

    def ajouter_membre(self, membre: MembreJury):
        AjouterMembreValidatorList(jury=self, membre=membre).validate()
        self.membres.append(membre)

    def recuperer_membre(self, uuid_membre: str) -> MembreJury:
        RecupererMembreValidatorList(uuid_membre=uuid_membre, jury=self).validate()
        for membre in self.membres:
            if membre.uuid == uuid_membre:
                return membre
        raise SignataireNonTrouveException

    def modifier_membre(self, membre: MembreJury):
        ModifierMembreValidatorList(jury=self, membre=membre).validate()
        ancien_membre = self.recuperer_membre(membre.uuid)
        if ancien_membre.est_promoteur:
            raise PromoteurModifieException(uuid_membre=membre.uuid, jury=self)
        self.membres.remove(ancien_membre)
        self.membres.append(membre)

    def retirer_membre(self, uuid_membre: str):
        RetirerMembreValidatorList(uuid_membre=uuid_membre, jury=self).validate()
        membre = self.recuperer_membre(uuid_membre)
        if membre.est_promoteur:
            raise PromoteurRetireException(uuid_membre=uuid_membre, jury=self)
        self.membres.remove(membre)

    def modifier_role_membre(self, uuid_membre: str, role: RoleJury):
        ModifierRoleMembreValidatorList(uuid_membre=uuid_membre, jury=self).validate()
        ancien_membre = self.recuperer_membre(uuid_membre)
        if ancien_membre.role not in {RoleJury.PRESIDENT, RoleJury.SECRETAIRE, RoleJury.MEMBRE}:
            raise PasUnMembreException()
        if ancien_membre.est_promoteur and role == RoleJury.PRESIDENT:
            raise PromoteurPresidentException()
        # Set the current president / secretary as a member
        if role != RoleJury.MEMBRE:
            for membre in self.membres:
                if membre.uuid != uuid_membre and membre.role == role:
                    self.membres.remove(membre)
                    self.membres.append(attr.evolve(membre, role=RoleJury.MEMBRE))
        self.membres.remove(ancien_membre)
        self.membres.append(attr.evolve(ancien_membre, role=role))

    def inviter_a_signer(self, verificateur: MembreJury):
        self._supprimer_membres_role(RoleJury.VERIFICATEUR)
        self._supprimer_membres_role(RoleJury.CDD)
        self._supprimer_membres_role(RoleJury.ADRE)
        self.membres.append(verificateur)

        etats_initiaux = [ChoixEtatSignature.NOT_INVITED, ChoixEtatSignature.DECLINED]
        for membre in filter(lambda m: m.signature.etat in etats_initiaux, self.membres):
            InviterASignerValidatorList(jury=self, signataire_id=membre.uuid).validate()
            self.membres = [m for m in self.membres if m.uuid != membre.uuid]
            self.membres.append(
                attr.evolve(
                    membre,
                    signature=attr.evolve(
                        membre.signature,
                        etat=ChoixEtatSignature.INVITED,
                        commentaire_externe="",
                        commentaire_interne="",
                        motif_refus="",
                    ),
                )
            )

    def approuver(
        self,
        signataire: MembreJury,
        commentaire_interne: Optional[str],
        commentaire_externe: Optional[str],
    ) -> None:
        ApprouverValidatorList(
            jury=self,
            signataire_id=signataire.uuid,
        ).validate()
        self.membres = [membre for membre in self.membres if membre.uuid != signataire.uuid]
        self.membres.append(
            attr.evolve(
                signataire,
                signature=attr.evolve(
                    signataire.signature,
                    etat=ChoixEtatSignature.APPROVED,
                    commentaire_interne=commentaire_interne or '',
                    commentaire_externe=commentaire_externe or '',
                ),
            )
        )

    def approuver_par_pdf(self, signataire: MembreJury, pdf: List[str]) -> None:
        ApprouverValidatorList(
            jury=self,
            signataire_id=signataire.uuid,
        ).validate()
        self.membres = [membre for membre in self.membres if membre.uuid != signataire.uuid]
        self.membres.append(
            attr.evolve(
                signataire,
                signature=attr.evolve(
                    signataire.signature,
                    etat=ChoixEtatSignature.APPROVED,
                    pdf=pdf,
                ),
            )
        )

    def refuser(
        self,
        signataire: MembreJury,
        commentaire_interne: Optional[str],
        commentaire_externe: Optional[str],
        motif_refus: Optional[str],
    ) -> None:
        ApprouverValidatorList(
            jury=self,
            signataire_id=signataire.uuid,
        ).validate()
        self.membres = [membre for membre in self.membres if membre.uuid != signataire.uuid]
        self.membres.append(
            attr.evolve(
                signataire,
                signature=attr.evolve(
                    signataire.signature,
                    etat=ChoixEtatSignature.DECLINED,
                    commentaire_interne=commentaire_interne or '',
                    commentaire_externe=commentaire_externe or '',
                    motif_refus=motif_refus or '',
                ),
            )
        )

    def refuser_par_cdd(
        self,
        signataire: MembreJury,
        commentaire_interne: Optional[str],
        commentaire_externe: Optional[str],
        motif_refus: Optional[str],
    ) -> None:
        self._supprimer_membres_role(RoleJury.CDD)
        self.reinitialiser_signatures()
        self.membres.append(
            attr.evolve(
                signataire,
                signature=attr.evolve(
                    signataire.signature,
                    etat=ChoixEtatSignature.DECLINED,
                    commentaire_interne=commentaire_interne or '',
                    commentaire_externe=commentaire_externe or '',
                    motif_refus=motif_refus or '',
                ),
            )
        )

    def approuver_par_cdd(
        self,
        signataire: MembreJury,
        commentaire_interne: Optional[str],
        commentaire_externe: Optional[str],
    ) -> None:
        self._supprimer_membres_role(RoleJury.CDD)
        self.membres.append(
            attr.evolve(
                signataire,
                signature=attr.evolve(
                    signataire.signature,
                    etat=ChoixEtatSignature.APPROVED,
                    commentaire_interne=commentaire_interne or '',
                    commentaire_externe=commentaire_externe or '',
                ),
            )
        )

    def refuser_par_adre(
        self,
        signataire: MembreJury,
        commentaire_interne: Optional[str],
        commentaire_externe: Optional[str],
        motif_refus: Optional[str],
    ) -> None:
        self._supprimer_membres_role(RoleJury.ADRE)
        self.reinitialiser_signatures()
        self.membres.append(
            attr.evolve(
                signataire,
                signature=attr.evolve(
                    signataire.signature,
                    etat=ChoixEtatSignature.DECLINED,
                    commentaire_interne=commentaire_interne or '',
                    commentaire_externe=commentaire_externe or '',
                    motif_refus=motif_refus or '',
                ),
            )
        )

    def approuver_par_adre(
        self,
        signataire: MembreJury,
        commentaire_interne: Optional[str],
        commentaire_externe: Optional[str],
    ) -> None:
        self._supprimer_membres_role(RoleJury.ADRE)
        self.membres.append(
            attr.evolve(
                signataire,
                signature=attr.evolve(
                    signataire.signature,
                    etat=ChoixEtatSignature.APPROVED,
                    commentaire_interne=commentaire_interne or '',
                    commentaire_externe=commentaire_externe or '',
                ),
            )
        )

    def reinitialiser_signatures(self) -> None:
        pass
        self.membres = [
            attr.evolve(
                membre,
                signature=SignatureMembre(),
            )
            for membre in self.membres
        ]
