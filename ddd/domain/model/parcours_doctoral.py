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
import uuid
from datetime import datetime
from typing import List, Optional, Union

import attr

from ddd.logic.reference.domain.model.bourse import BourseIdentity
from osis_common.ddd import interface
from parcours_doctoral.ddd.domain.model._cotutelle import Cotutelle
from parcours_doctoral.ddd.domain.model._experience_precedente_recherche import (
    ExperiencePrecedenteRecherche,
    aucune_experience_precedente_recherche,
)
from parcours_doctoral.ddd.domain.model._financement import Financement
from parcours_doctoral.ddd.domain.model._formation import FormationIdentity
from parcours_doctoral.ddd.domain.model._institut import InstitutIdentity
from parcours_doctoral.ddd.domain.model._projet import Projet
from parcours_doctoral.ddd.domain.model.enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixDoctoratDejaRealise,
    ChoixSousDomaineSciences,
    ChoixStatutParcoursDoctoral,
    ChoixTypeFinancement,
)
from parcours_doctoral.ddd.domain.validator.validator_by_business_action import (
    ModifierFinancementValidatorList,
    ProjetDoctoralValidatorList,
)
from parcours_doctoral.ddd.jury.domain.model.enums import ChoixEtatSignature

ENTITY_CDE = 'CDE'
ENTITY_CDSS = 'CDSS'
ENTITY_CLSM = 'CLSM'
ENTITY_SCIENCES = 'CDSC'
SIGLE_SCIENCES = 'SC3DP'

COMMISSIONS_CDE_CLSM = {ENTITY_CDE, ENTITY_CLSM}
COMMISSIONS_CDSS = {ENTITY_CDSS}
SIGLES_SCIENCES = {SIGLE_SCIENCES}


@attr.dataclass(frozen=True, slots=True)
class ParcoursDoctoralIdentity(interface.EntityIdentity):
    uuid: str


@attr.dataclass(slots=True, hash=False, eq=False)
class ParcoursDoctoral(interface.RootEntity):
    entity_id: ParcoursDoctoralIdentity
    statut: ChoixStatutParcoursDoctoral

    projet: 'Projet'
    cotutelle: 'Cotutelle'
    financement: 'Financement'
    experience_precedente_recherche: 'ExperiencePrecedenteRecherche'

    formation_id: FormationIdentity
    matricule_doctorant: str
    reference: int
    bourse_recherche: Optional[BourseIdentity] = None
    autre_bourse_recherche: Optional[str] = ''
    commission_proximite: Optional[
        Union[
            ChoixCommissionProximiteCDEouCLSM,
            ChoixCommissionProximiteCDSS,
            ChoixSousDomaineSciences,
        ]
    ] = None
    justification: str = ''
    titre_these_propose: str = ''

    def verrouiller_parcours_doctoral_pour_signature(self):
        self.statut = ChoixStatutParcoursDoctoral.EN_ATTENTE_DE_SIGNATURE

    @property
    def est_verrouillee_pour_signature(self) -> bool:
        return self.statut == ChoixStatutParcoursDoctoral.EN_ATTENTE_DE_SIGNATURE

    def verifier_projet_doctoral(self):
        """Vérification de la validité du projet doctoral avant demande des signatures"""
        ProjetDoctoralValidatorList(
            self.projet,
            self.financement,
            self.experience_precedente_recherche,
            self.cotutelle,
        ).validate()

    def soumettre_epreuve_confirmation(self):
        self.statut = ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE

    def encoder_decision_reussite_epreuve_confirmation(self):
        self.statut = ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE

    def encoder_decision_echec_epreuve_confirmation(self):
        self.statut = ChoixStatutParcoursDoctoral.NON_AUTORISE_A_POURSUIVRE

    def encoder_decision_repassage_epreuve_confirmation(self):
        self.statut = ChoixStatutParcoursDoctoral.CONFIRMATION_A_REPRESENTER

    def _modifier_projet(
        self,
        titre: str,
        resume: str,
        langue_redaction_these: str,
        institut_these: str,
        lieu_these: str,
        deja_commence: Optional[bool],
        deja_commence_institution: str,
        date_debut: Optional[datetime.date],
        documents: List[str],
        graphe_gantt: List[str],
        proposition_programme_doctoral: List[str],
        projet_formation_complementaire: List[str],
        lettres_recommandation: List[str],
    ):
        self.projet = Projet(
            titre=titre,
            resume=resume,
            langue_redaction_these=langue_redaction_these,
            institut_these=InstitutIdentity(uuid.UUID(institut_these)) if institut_these else None,
            lieu_these=lieu_these,
            documents=documents,
            graphe_gantt=graphe_gantt,
            proposition_programme_doctoral=proposition_programme_doctoral,
            projet_formation_complementaire=projet_formation_complementaire,
            lettres_recommandation=lettres_recommandation,
            deja_commence=deja_commence,
            deja_commence_institution=deja_commence_institution,
            date_debut=date_debut,
        )

    def _modifier_financement(
        self,
        type: Optional[str],
        type_contrat_travail: str,
        eft: Optional[int],
        bourse_recherche: Optional[BourseIdentity],
        autre_bourse_recherche: str,
        bourse_date_debut: Optional[datetime.date],
        bourse_date_fin: Optional[datetime.date],
        bourse_preuve: List[str],
        duree_prevue: Optional[int],
        temps_consacre: Optional[int],
        est_lie_fnrs_fria_fresh_csc: Optional[bool],
        commentaire: str,
    ):
        self.financement = Financement(
            type=ChoixTypeFinancement[type] if type else None,
            type_contrat_travail=type_contrat_travail,
            eft=eft,
            bourse_recherche=bourse_recherche,
            autre_bourse_recherche=autre_bourse_recherche,
            bourse_date_debut=bourse_date_debut,
            bourse_date_fin=bourse_date_fin,
            bourse_preuve=bourse_preuve,
            duree_prevue=duree_prevue,
            temps_consacre=temps_consacre,
            est_lie_fnrs_fria_fresh_csc=est_lie_fnrs_fria_fresh_csc,
            commentaire=commentaire,
        )

    def _modifier_experience_precedente(
        self,
        doctorat_deja_realise: str,
        institution: str,
        domaine_these: str,
        date_soutenance: Optional[datetime.date],
        raison_non_soutenue: str,
    ):
        if doctorat_deja_realise == ChoixDoctoratDejaRealise.NO.name or not doctorat_deja_realise:
            self.experience_precedente_recherche = aucune_experience_precedente_recherche
        else:
            self.experience_precedente_recherche = ExperiencePrecedenteRecherche(
                doctorat_deja_realise=ChoixDoctoratDejaRealise[doctorat_deja_realise],
                institution=institution or '',
                domaine_these=domaine_these or '',
                date_soutenance=date_soutenance,
                raison_non_soutenue=raison_non_soutenue or '',
            )

    def modifier_projet(
        self,
        langue_redaction_these: str,
        institut_these: str,
        lieu_these: str,
        titre: str,
        resume: str,
        doctorat_deja_realise: str,
        institution: str,
        domaine_these: str,
        date_soutenance: Optional[datetime.date],
        raison_non_soutenue: str,
        projet_doctoral_deja_commence: Optional[bool],
        projet_doctoral_institution: str,
        projet_doctoral_date_debut: Optional[datetime.date],
        documents: List[str],
        graphe_gantt: List[str],
        proposition_programme_doctoral: List[str],
        projet_formation_complementaire: List[str],
        lettres_recommandation: List[str],
    ) -> None:
        self._modifier_projet(
            titre=titre,
            resume=resume,
            langue_redaction_these=langue_redaction_these,
            institut_these=institut_these,
            lieu_these=lieu_these,
            deja_commence=projet_doctoral_deja_commence,
            deja_commence_institution=projet_doctoral_institution,
            date_debut=projet_doctoral_date_debut,
            documents=documents,
            graphe_gantt=graphe_gantt,
            proposition_programme_doctoral=proposition_programme_doctoral,
            projet_formation_complementaire=projet_formation_complementaire,
            lettres_recommandation=lettres_recommandation,
        )
        self._modifier_experience_precedente(
            doctorat_deja_realise=doctorat_deja_realise,
            institution=institution,
            domaine_these=domaine_these,
            date_soutenance=date_soutenance,
            raison_non_soutenue=raison_non_soutenue,
        )

    def modifier_financement(
        self,
        type: Optional[str],
        type_contrat_travail: Optional[str],
        eft: Optional[int],
        bourse_recherche: Optional[BourseIdentity],
        autre_bourse_recherche: Optional[str],
        bourse_date_debut: Optional[datetime.date],
        bourse_date_fin: Optional[datetime.date],
        bourse_preuve: List[str],
        duree_prevue: Optional[int],
        temps_consacre: Optional[int],
        est_lie_fnrs_fria_fresh_csc: Optional[bool],
        commentaire: Optional[str],
    ) -> None:
        ModifierFinancementValidatorList(
            type=type,
            type_contrat_travail=type_contrat_travail,
        ).validate()
        self._modifier_financement(
            type=type,
            type_contrat_travail=type_contrat_travail,
            eft=eft,
            bourse_recherche=bourse_recherche,
            autre_bourse_recherche=autre_bourse_recherche,
            bourse_date_debut=bourse_date_debut,
            bourse_date_fin=bourse_date_fin,
            bourse_preuve=bourse_preuve,
            duree_prevue=duree_prevue,
            temps_consacre=temps_consacre,
            est_lie_fnrs_fria_fresh_csc=est_lie_fnrs_fria_fresh_csc,
            commentaire=commentaire,
        )

    def modifier_cotutelle(
        self,
        motivation: Optional[str],
        institution_fwb: Optional[bool],
        institution: Optional[str],
        autre_institution_nom: Optional[str],
        autre_institution_adresse: Optional[str],
        demande_ouverture: List[str],
        convention: List[str],
        autres_documents: List[str],
    ):
        self.cotutelle = Cotutelle(
            motivation=motivation,
            institution_fwb=institution_fwb,
            institution=institution,
            autre_institution_nom=autre_institution_nom,
            autre_institution_adresse=autre_institution_adresse,
            demande_ouverture=demande_ouverture,
            convention=convention,
            autres_documents=autres_documents,
        )

    def verrouiller_jury_pour_signature(self):
        self.statut = ChoixStatutParcoursDoctoral.JURY_SOUMIS

    def deverrouiller_jury_apres_refus(self):
        self.statut = ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE

    def deverrouiller_jury_apres_reinitialisation(self):
        self.statut = ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE

    def approuver_jury_par_cdd(self):
        self.statut = ChoixStatutParcoursDoctoral.JURY_APPROUVE_CDD

    def refuser_jury_par_cdd(self):
        self.statut = ChoixStatutParcoursDoctoral.JURY_REFUSE_CDD

    def approuver_jury_par_adre(self):
        self.statut = ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE

    def refuser_jury_par_adre(self):
        self.statut = ChoixStatutParcoursDoctoral.JURY_REFUSE_ADRE

    def changer_statut_si_approbation_jury(self, jury: 'Jury'):
        if all(member.signature.etat == ChoixEtatSignature.APPROVED for member in jury.membres):
            self.statut = ChoixStatutParcoursDoctoral.JURY_APPROUVE_CA

    def soumettre_defense_privee(self, titre_these: str):
        self.statut = ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE
        self.titre_these_propose = titre_these
