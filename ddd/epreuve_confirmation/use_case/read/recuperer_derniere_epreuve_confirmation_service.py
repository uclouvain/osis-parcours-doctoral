# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from parcours_doctoral.ddd.builder.parcours_doctoral_identity import ParcoursDoctoralIdentityBuilder
from parcours_doctoral.ddd.epreuve_confirmation.commands import (
    RecupererDerniereEpreuveConfirmationQuery,
)
from parcours_doctoral.ddd.epreuve_confirmation.dtos import EpreuveConfirmationDTO
from parcours_doctoral.ddd.epreuve_confirmation.repository.i_epreuve_confirmation import (
    IEpreuveConfirmationRepository,
)
from parcours_doctoral.ddd.repository.i_doctorat import IParcoursDoctoralRepository


def recuperer_derniere_epreuve_confirmation(
    cmd: 'RecupererDerniereEpreuveConfirmationQuery',
    epreuve_confirmation_repository: 'IEpreuveConfirmationRepository',
    doctorat_repository: 'IParcoursDoctoralRepository',
) -> EpreuveConfirmationDTO:
    # GIVEN
    doctorat_id = ParcoursDoctoralIdentityBuilder.build_from_uuid(cmd.doctorat_uuid)
    doctorat_repository.verifier_existence(doctorat_id)

    # THEN
    return epreuve_confirmation_repository.get_dto_by_doctorat_identity(doctorat_id)
