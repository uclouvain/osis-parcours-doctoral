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
from typing import List, Optional
from uuid import UUID, uuid4

import attr

from osis_common.ddd import interface
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.enums import (
    ChoixEtatSignature,
    ChoixStatutAutorisationDiffusionThese,
    RoleActeur,
    TypeModalitesDiffusionThese,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.validator.validator_by_business_action import (
    AutorisationDiffusionTheseValidatorList,
)


@attr.dataclass(frozen=True, slots=True, eq=True, hash=True)
class SignatureAutorisationDiffusionThese(interface.ValueObject):
    etat: ChoixEtatSignature = ChoixEtatSignature.NOT_INVITED
    date: Optional[datetime.datetime] = None
    commentaire_externe: str = ''
    commentaire_interne: str = ''
    motif_refus: str = ''


@attr.dataclass(frozen=True, slots=True, eq=True, hash=True)
class SignataireAutorisationDiffusionThese(interface.ValueObject):
    matricule: str
    role: 'RoleActeur'
    uuid: UUID = attr.Factory(uuid4)
    signature: SignatureAutorisationDiffusionThese = attr.Factory(SignatureAutorisationDiffusionThese)


@attr.dataclass(frozen=True, slots=True)
class AutorisationDiffusionTheseIdentity(interface.EntityIdentity):
    uuid: UUID


@attr.dataclass(slots=True, hash=False, eq=False)
class AutorisationDiffusionThese(interface.RootEntity):
    entity_id: 'AutorisationDiffusionTheseIdentity'

    statut: ChoixStatutAutorisationDiffusionThese = ChoixStatutAutorisationDiffusionThese.DIFFUSION_NON_SOUMISE

    sources_financement: str = ''
    resume_anglais: str = ''
    resume_autre_langue: str = ''
    langue_redaction_these: str = ''
    mots_cles: list[str] = attr.Factory(list)
    type_modalites_diffusion: TypeModalitesDiffusionThese | None = None
    date_embargo: datetime.date | None = None
    limitations_additionnelles_chapitres: str = ''

    modalites_diffusion_acceptees: str = ''
    modalites_diffusion_acceptees_le: datetime.date | None = None

    signataires: List[SignataireAutorisationDiffusionThese] = attr.Factory(list)

    def encoder_formulaire(
        self,
        sources_financement: str,
        resume_anglais: str,
        resume_autre_langue: str,
        langue_redaction_these: str,
        mots_cles: list[str],
        type_modalites_diffusion: str,
        date_embargo: datetime.date | None,
        limitations_additionnelles_chapitres: str,
        modalites_diffusion_acceptees: str,
    ):
        self.sources_financement = sources_financement
        self.resume_anglais = resume_anglais
        self.resume_autre_langue = resume_autre_langue
        self.langue_redaction_these = langue_redaction_these
        self.mots_cles = mots_cles
        self.type_modalites_diffusion = (
            TypeModalitesDiffusionThese[type_modalites_diffusion] if type_modalites_diffusion else None
        )
        self.limitations_additionnelles_chapitres = limitations_additionnelles_chapitres
        self.date_embargo = date_embargo
        self.modalites_diffusion_acceptees = modalites_diffusion_acceptees
        self.modalites_diffusion_acceptees_le = datetime.date.today() if modalites_diffusion_acceptees else None

    def envoyer_formulaire_au_promoteur(self):
        self.statut = ChoixStatutAutorisationDiffusionThese.DIFFUSION_SOUMISE

        AutorisationDiffusionTheseValidatorList(
            sources_financement=self.sources_financement,
            resume_anglais=self.resume_anglais,
            langue_redaction_these=self.langue_redaction_these,
            mots_cles=self.mots_cles,
            type_modalites_diffusion=self.type_modalites_diffusion,
            date_embargo=self.date_embargo,
            modalites_diffusion_acceptees=self.modalites_diffusion_acceptees,
            modalites_diffusion_acceptees_le=self.modalites_diffusion_acceptees_le,
        ).validate()
