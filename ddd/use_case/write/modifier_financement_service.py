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
from ddd.logic.reference.domain.builder.bourse_identity import BourseIdentityBuilder
from parcours_doctoral.ddd.builder.parcours_doctoral_identity import (
    ParcoursDoctoralIdentityBuilder,
)
from parcours_doctoral.ddd.commands import (
    ModifierFinancementCommand,
    ModifierProjetCommand,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.domain.service.i_historique import IHistorique
from parcours_doctoral.ddd.repository.i_parcours_doctoral import (
    IParcoursDoctoralRepository,
)


def modifier_financement(
    cmd: 'ModifierFinancementCommand',
    parcours_doctoral_repository: 'IParcoursDoctoralRepository',
    historique: 'IHistorique',
) -> 'ParcoursDoctoralIdentity':
    # GIVEN
    entity_id = ParcoursDoctoralIdentityBuilder.build_from_uuid(cmd.uuid)
    parcours_doctoral = parcours_doctoral_repository.get(entity_id=entity_id)
    bourse_recherche_id = BourseIdentityBuilder.build_from_uuid(cmd.bourse_recherche) if cmd.bourse_recherche else None

    # WHEN
    parcours_doctoral.modifier_financement(
        type=cmd.type,
        type_contrat_travail=cmd.type_contrat_travail,
        eft=cmd.eft,
        bourse_recherche=bourse_recherche_id,
        autre_bourse_recherche=cmd.autre_bourse_recherche,
        bourse_date_debut=cmd.bourse_date_debut,
        bourse_date_fin=cmd.bourse_date_fin,
        bourse_preuve=cmd.bourse_preuve,
        duree_prevue=cmd.duree_prevue,
        temps_consacre=cmd.temps_consacre,
        est_lie_fnrs_fria_fresh_csc=cmd.est_lie_fnrs_fria_fresh_csc,
        commentaire=cmd.commentaire,
    )

    # THEN
    parcours_doctoral_repository.save(parcours_doctoral)
    historique.historiser_modification_projet(parcours_doctoral, cmd.matricule_auteur)

    return entity_id
