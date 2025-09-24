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
from parcours_doctoral.ddd.builder.parcours_doctoral_identity import (
    ParcoursDoctoralIdentityBuilder,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.domain.service.i_historique import IHistorique
from parcours_doctoral.ddd.repository.i_parcours_doctoral import (
    IParcoursDoctoralRepository,
)
from parcours_doctoral.ddd.soutenance_publique.commands import (
    SoumettreSoutenancePubliqueCommand,
)


def soumettre_soutenance_publique(
    cmd: 'SoumettreSoutenancePubliqueCommand',
    parcours_doctoral_repository: 'IParcoursDoctoralRepository',
    historique: 'IHistorique',
) -> ParcoursDoctoralIdentity:
    # GIVEN
    parcours_doctoral_identity = ParcoursDoctoralIdentityBuilder.build_from_uuid(uuid=cmd.uuid_parcours_doctoral)
    parcours_doctoral = parcours_doctoral_repository.get(parcours_doctoral_identity)
    statut_original_parcours_doctoral = parcours_doctoral.statut

    # WHEN
    parcours_doctoral.soumettre_soutenance_publique(
        langue=cmd.langue,
        autre_langue=cmd.autre_langue,
        date_heure=cmd.date_heure,
        lieu=cmd.lieu,
        local_deliberation=cmd.local_deliberation,
        resume_annonce=cmd.resume_annonce,
        photo_annonce=cmd.photo_annonce,
    )

    # THEN
    parcours_doctoral_repository.save(parcours_doctoral)
    historique.historiser_soumission_soutenance_publique(
        parcours_doctoral=parcours_doctoral,
        matricule_auteur=cmd.matricule_auteur,
        statut_original_parcours_doctoral=statut_original_parcours_doctoral,
    )

    return parcours_doctoral_identity
