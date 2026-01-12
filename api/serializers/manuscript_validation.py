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

from base.utils.serializers import DTOSerializer
from parcours_doctoral.ddd.autorisation_diffusion_these.commands import (
    AccepterTheseParPromoteurReferenceCommand,
    RefuserTheseParPromoteurReferenceCommand,
)

__all__ = [
    'AcceptThesisByLeadPromoterSerializer',
    'RejectThesisByLeadPromoterSerializer',
]


class RejectThesisByLeadPromoterSerializer(DTOSerializer):
    """Contains the submitted data to reject the thesis by the lead supervisor."""

    uuid_parcours_doctoral = None
    matricule_promoteur = None

    class Meta:
        source = RefuserTheseParPromoteurReferenceCommand


class AcceptThesisByLeadPromoterSerializer(DTOSerializer):
    """Contains the submitted data to accept the thesis by the lead supervisor."""

    uuid_parcours_doctoral = None
    matricule_promoteur = None

    class Meta:
        source = AccepterTheseParPromoteurReferenceCommand
