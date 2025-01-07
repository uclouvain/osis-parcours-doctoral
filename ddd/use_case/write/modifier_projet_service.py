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
from parcours_doctoral.ddd.commands import ModifierProjetCommand
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.domain.service.i_historique import IHistorique
from parcours_doctoral.ddd.repository.i_parcours_doctoral import (
    IParcoursDoctoralRepository,
)


def modifier_projet(
    cmd: 'ModifierProjetCommand',
    parcours_doctoral_repository: 'IParcoursDoctoralRepository',
    historique: 'IHistorique',
) -> 'ParcoursDoctoralIdentity':
    # GIVEN
    entity_id = ParcoursDoctoralIdentityBuilder.build_from_uuid(cmd.uuid)
    parcours_doctoral = parcours_doctoral_repository.get(entity_id=entity_id)
    bourse_recherche_id = BourseIdentityBuilder.build_from_uuid(cmd.bourse_recherche) if cmd.bourse_recherche else None

    # WHEN
    parcours_doctoral.modifier_projet(
        type_financement=cmd.type_financement,
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
        commentaire_financement=cmd.commentaire_financement,
        titre=cmd.titre_projet,
        resume=cmd.resume_projet,
        langue_redaction_these=cmd.langue_redaction_these,
        institut_these=cmd.institut_these,
        lieu_these=cmd.lieu_these,
        projet_doctoral_deja_commence=cmd.projet_doctoral_deja_commence,
        projet_doctoral_institution=cmd.projet_doctoral_institution,
        projet_doctoral_date_debut=cmd.projet_doctoral_date_debut,
        documents=cmd.documents_projet,
        graphe_gantt=cmd.graphe_gantt,
        proposition_programme_doctoral=cmd.proposition_programme_doctoral,
        projet_formation_complementaire=cmd.projet_formation_complementaire,
        lettres_recommandation=cmd.lettres_recommandation,
        doctorat_deja_realise=cmd.doctorat_deja_realise,
        institution=cmd.institution,
        domaine_these=cmd.domaine_these,
        date_soutenance=cmd.date_soutenance,
        raison_non_soutenue=cmd.raison_non_soutenue,
    )

    # THEN
    parcours_doctoral_repository.save(parcours_doctoral)
    historique.historiser_modification_projet(parcours_doctoral, cmd.matricule_auteur)

    return entity_id
