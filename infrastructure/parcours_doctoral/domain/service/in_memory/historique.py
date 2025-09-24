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
from email.message import EmailMessage
from typing import Optional

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from ddd.logic.shared_kernel.personne_connue_ucl.dtos import PersonneConnueUclDTO
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.domain.model.groupe_de_supervision import (
    GroupeDeSupervision,
    SignataireIdentity,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoral,
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.domain.service.i_historique import IHistorique
from parcours_doctoral.ddd.dtos import AvisDTO


class HistoriqueInMemory(IHistorique):
    @classmethod
    def historiser_message_au_doctorant(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_emetteur: str,
        message: EmailMessage,
    ):
        pass

    @classmethod
    def historiser_initialisation(cls, parcours_doctoral: ParcoursDoctoralIdentity):
        pass

    @classmethod
    def historiser_demande_signatures(cls, parcours_doctoral: ParcoursDoctoral, matricule_auteur: str):
        pass

    @classmethod
    def historiser_designation_promoteur_reference(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        signataire_id: 'SignataireIdentity',
        matricule_auteur: str,
    ):
        pass

    @classmethod
    def historiser_ajout_membre(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        groupe_de_supervision: GroupeDeSupervision,
        signataire_id: 'SignataireIdentity',
        matricule_auteur: str,
    ):
        pass

    @classmethod
    def historiser_suppression_membre(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        groupe_de_supervision: GroupeDeSupervision,
        signataire_id: 'SignataireIdentity',
        matricule_auteur: str,
    ):
        pass

    @classmethod
    def historiser_modification_membre(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        signataire_id: 'SignataireIdentity',
        matricule_auteur: str,
    ):
        pass

    @classmethod
    def historiser_modification_projet(cls, parcours_doctoral: ParcoursDoctoral, matricule_auteur: str):
        pass

    @classmethod
    def historiser_modification_cotutelle(
        cls,
        parcours_doctoral_identity: ParcoursDoctoralIdentity,
        matricule_auteur: str,
    ):
        pass

    @classmethod
    def historiser_avis(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        signataire_id: 'SignataireIdentity',
        avis: AvisDTO,
        statut_original_proposition: 'ChoixStatutPropositionDoctorale',
        matricule_auteur: Optional[str] = '',
    ):
        pass

    @classmethod
    def historiser_repassage_epreuve_confirmation(cls, parcours_doctoral: ParcoursDoctoral, matricule_auteur: str):
        pass

    @classmethod
    def historiser_echec_epreuve_confirmation(cls, parcours_doctoral: ParcoursDoctoral, matricule_auteur: str):
        pass

    @classmethod
    def historiser_reussite_epreuve_confirmation(cls, parcours_doctoral: ParcoursDoctoral, matricule_auteur: str):
        pass

    @classmethod
    def historiser_soumission_epreuve_confirmation(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_auteur: str,
        statut_original_parcours_doctoral: ChoixStatutParcoursDoctoral,
    ):
        pass

    @classmethod
    def historiser_soumission_defense_privee(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_auteur: str,
        statut_original_parcours_doctoral: ChoixStatutParcoursDoctoral,
    ):
        pass

    @classmethod
    def historiser_soumission_proces_verbal_defense_privee(
        cls,
        parcours_doctoral_identity: ParcoursDoctoralIdentity,
        matricule_auteur: str,
    ):
        pass

    @classmethod
    def historiser_autorisation_defense_privee(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_auteur: str,
    ):
        pass

    @classmethod
    def historiser_invitation_jury_defense_privee(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        auteur: PersonneConnueUclDTO,
    ):
        pass

    @classmethod
    def historiser_decision_reussie_defense_privee(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_auteur: str,
    ):
        pass

    @classmethod
    def historiser_decision_echec_defense_privee(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_auteur: str,
    ):
        pass

    @classmethod
    def historiser_decision_repetition_defense_privee(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_auteur: str,
    ):
        pass

    @classmethod
    def historiser_modification_defense_privee(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_auteur: str,
    ):
        pass

    @classmethod
    def historiser_soumission_soutenance_publique(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_auteur: str,
        statut_original_parcours_doctoral: ChoixStatutParcoursDoctoral,
    ):
        pass

    @classmethod
    def historiser_autorisation_soutenance_publique(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_auteur: str,
    ):
        pass
