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
from typing import Union

import attr

from base.ddd.utils.business_validator import BusinessValidator
from parcours_doctoral.ddd.jury.domain.model.enums import ChoixEtatSignature
from parcours_doctoral.ddd.jury.domain.validator.exceptions import (
    SignataireDejaInviteException,
)


@attr.dataclass(frozen=True, slots=True)
class ShouldSignatairePasDejaInvite(BusinessValidator):
    jury: 'Jury'
    signataire_id: str

    def validate(self, *args, **kwargs):  # pragma: no cover
        etats_initiaux = [ChoixEtatSignature.NOT_INVITED, ChoixEtatSignature.DECLINED]
        if any(
            membre
            for membre in self.jury.membres
            if membre.uuid == self.signataire_id and membre.signature.etat not in etats_initiaux
        ):
            raise SignataireDejaInviteException
