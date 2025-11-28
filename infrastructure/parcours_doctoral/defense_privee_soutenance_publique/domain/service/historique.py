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

from osis_history.utilities import add_history_entry

from infrastructure.shared_kernel.personne_connue_ucl.personne_connue_ucl import (
    PersonneConnueUclTranslator,
)
from parcours_doctoral.ddd.defense_privee_soutenance_publique.domain.service.i_historique import (
    IHistorique,
)
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoral


class Historique(IHistorique):
    @classmethod
    def historiser_soumission_formulaire_par_candidat(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_auteur: str,
        statut_original_parcours_doctoral: ChoixStatutParcoursDoctoral,
    ):
        if parcours_doctoral.statut != statut_original_parcours_doctoral:
            auteur = PersonneConnueUclTranslator().get(matricule_auteur)
            tags = ['parcours_doctoral', 'private-public-defenses', 'status-changed']

            add_history_entry(
                parcours_doctoral.entity_id.uuid,
                'Le doctorant a renseigné des informations relatives à la défense privée et à la soutenance publique.',
                'The doctoral student has filled in information relating to the private defence and to '
                'the public defences.',
                '{auteur.prenom} {auteur.nom}'.format(auteur=auteur),
                tags=tags,
            )

    @classmethod
    def historiser_autorisation_defense_privee_et_soutenance_publique(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_auteur: str,
    ):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        tags = ['parcours_doctoral', 'private-public-defenses', 'status-changed']

        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            'La défense privée et la soutenance publique ont été autorisées.',
            'The private and public defences have been authorised.',
            '{auteur.prenom} {auteur.nom}'.format(auteur=auteur),
            tags=tags,
        )

    @classmethod
    def historiser_decision_reussie_defense_privee_et_soutenance_publique(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_auteur: str,
    ):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        tags = ['parcours_doctoral', 'private-public-defenses', 'status-changed']

        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            'Les décisions de la défense privée et de la soutenance publique ont été données : celles-ci ont été '
            'réussies.',
            'The decisions of the private and public defences have been made: they have been passed.',
            '{auteur.prenom} {auteur.nom}'.format(auteur=auteur),
            tags=tags,
        )
