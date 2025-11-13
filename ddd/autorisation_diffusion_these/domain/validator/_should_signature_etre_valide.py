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

import attr

from base.ddd.utils.business_validator import BusinessValidator
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.enums import (
    ChoixEtatSignature,
    RoleActeur,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.validator.exceptions import (
    MotifRefusNonSpecifieException,
    NonPromoteurException,
    SignataireNonInviteException,
)

__all__ = [
    'ShouldSignataireEtrePromoteur',
    'ShouldSignataireEtreInvite',
    'ShouldMotifRefusEtreSpecifie',
]


@attr.dataclass(frozen=True, slots=True)
class ShouldSignataireEtrePromoteur(BusinessValidator):
    signataire: 'SignataireAutorisationDiffusionThese'

    def validate(self, *args, **kwargs):
        if self.signataire.entity_id.role != RoleActeur.PROMOTEUR:
            raise NonPromoteurException


@attr.dataclass(frozen=True, slots=True)
class ShouldSignataireEtreInvite(BusinessValidator):
    signataire: 'SignataireAutorisationDiffusionThese'

    def validate(self, *args, **kwargs):
        if self.signataire.signature.etat != ChoixEtatSignature.INVITED:
            raise SignataireNonInviteException


@attr.dataclass(frozen=True, slots=True)
class ShouldMotifRefusEtreSpecifie(BusinessValidator):
    motifs_refus: str

    def validate(self, *args, **kwargs):
        if not self.motifs_refus:
            raise MotifRefusNonSpecifieException
