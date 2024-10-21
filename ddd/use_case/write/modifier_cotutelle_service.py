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

from parcours_doctoral.ddd.commands import ModifierCotutelleCommand
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.domain.service.i_historique import IHistorique
from parcours_doctoral.ddd.repository.i_parcours_doctoral import (
    IParcoursDoctoralRepository,
)


def modifier_cotutelle(
    cmd: 'ModifierCotutelleCommand',
    parcours_doctoral_repository: 'IParcoursDoctoralRepository',
    historique: 'IHistorique',
) -> 'ParcoursDoctoralIdentity':
    # GIVEN
    parcours_doctoral_identity = ParcoursDoctoralIdentity(uuid=cmd.uuid_proposition)
    parcours_doctoral = parcours_doctoral_repository.get(parcours_doctoral_identity)

    # WHEN
    parcours_doctoral.modifier_cotutelle(
        motivation=cmd.motivation,
        institution_fwb=cmd.institution_fwb,
        institution=cmd.institution,
        autre_institution_nom=cmd.autre_institution_nom,
        autre_institution_adresse=cmd.autre_institution_adresse,
        demande_ouverture=cmd.demande_ouverture,
        convention=cmd.convention,
        autres_documents=cmd.autres_documents,
    )

    # THEN
    parcours_doctoral_repository.save(parcours_doctoral)
    historique.historiser_modification_cotutelle(parcours_doctoral_identity, cmd.matricule_auteur)

    return parcours_doctoral_identity
