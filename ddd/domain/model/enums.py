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
import itertools

from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from base.models.utils.utils import ChoiceEnum


class ChoixStatutParcoursDoctoral(ChoiceEnum):
    # Après création
    ADMIS = _('ADMIS')
    # Groupe de supervision
    EN_ATTENTE_DE_SIGNATURE = _('EN_ATTENTE_DE_SIGNATURE')
    # Confirmation exam
    CONFIRMATION_SOUMISE = _('CONFIRMATION_SOUMISE')
    CONFIRMATION_REUSSIE = _('CONFIRMATION_REUSSIE')
    NON_AUTORISE_A_POURSUIVRE = _('NON_AUTORISE_A_POURSUIVRE')
    CONFIRMATION_A_REPRESENTER = _('CONFIRMATION_A_REPRESENTER')
    # Jury
    JURY_SOUMIS = _('JURY_SOUMIS')
    JURY_APPROUVE_CA = _('JURY_APPROUVE_CA')
    JURY_APPROUVE_CDD = _('JURY_APPROUVE_CDD')
    JURY_REFUSE_CDD = _('JURY_REFUSE_CDD')
    JURY_APPROUVE_ADRE = _('JURY_APPROUVE_ADRE')
    JURY_REFUSE_ADRE = _('JURY_REFUSE_ADRE')
    # Défense privée
    DEFENSE_PRIVEE_SOUMISE = _('DEFENSE_PRIVEE_SOUMISE')
    DEFENSE_PRIVEE_AUTORISEE = _('DEFENSE_PRIVEE_AUTORISEE')
    DEFENSE_PRIVEE_A_RECOMMENCER = _('DEFENSE_PRIVEE_A_RECOMMENCER')
    DEFENSE_PRIVEE_REUSSIE = _('DEFENSE_PRIVEE_REUSSIE')
    DEFENSE_PRIVEE_EN_ECHEC = _('DEFENSE_PRIVEE_EN_ECHEC')
    # Autres
    ABANDON = _('ABANDON')


STATUTS_DOCTORAT_EPREUVE_CONFIRMATION_EN_COURS = {
    ChoixStatutParcoursDoctoral.ADMIS.name,
    ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name,
    ChoixStatutParcoursDoctoral.CONFIRMATION_A_REPRESENTER.name,
}


STATUTS_DOCTORAT_DEFENSE_PRIVEE_EN_COURS = {
    ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE.name,
    ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_AUTORISEE.name,
    ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE.name,
    ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_A_RECOMMENCER.name,
}


class ChoixLangueDefense(ChoiceEnum):
    FRENCH = _('French')
    ENGLISH = _('English')
    OTHER = _('Other')
    UNDECIDED = _('Undecided')


class ChoixDoctoratDejaRealise(ChoiceEnum):
    YES = _('YES')
    NO = _('NO')


class ChoixTypeFinancement(ChoiceEnum):
    WORK_CONTRACT = _('WORK_CONTRACT')
    SEARCH_SCHOLARSHIP = _('SEARCH_SCHOLARSHIP')
    SELF_FUNDING = _('SELF_FUNDING')


class BourseRecherche(ChoiceEnum):
    OTHER = _('OTHER')


class ChoixStatutSignatureGroupeDeSupervision(ChoiceEnum):
    IN_PROGRESS = _('IN_PROGRESS')
    SIGNING_IN_PROGRESS = _('SIGNING_IN_PROGRESS')


class ChoixEtatSignature(ChoiceEnum):
    NOT_INVITED = _('NOT_INVITED')  # Pas encore envoyée au signataire
    INVITED = _('INVITED')  # Envoyée au signataire
    APPROVED = pgettext_lazy("admission decision", "Approved")  # Approuvée par le signataire
    DECLINED = pgettext_lazy("admission decision", "Denied")  # Refusée par le signataire


class ChoixCommissionProximiteCDEouCLSM(ChoiceEnum):
    ECONOMY = _('ECONOMY')
    MANAGEMENT = _('MANAGEMENT')


class ChoixCommissionProximiteCDSS(ChoiceEnum):
    ECLI = _("Proximity commission for experimental and clinical research (ECLI)")
    BCGIM = _("Proximity commission for biochemistry, cellular and molecular biology, genetics, immunology (BCGIM)")
    NRSC = _("Proximity Commission for Neuroscience (NRSC)")
    SPSS = _("Proximity commission for public health, health and society (SPSS)")
    DENT = _("Proximity Commission for Dental Sciences (DENT)")
    DFAR = _("Proximity Commission for Pharmaceutical Sciences (DFAR)")
    MOTR = _("Proximity Commission for Motricity Sciences (MOTR)")


class ChoixSousDomaineSciences(ChoiceEnum):
    PHYSICS = _("PHYSICS")
    CHEMISTRY = _("CHEMISTRY")
    MATHEMATICS = _("MATHEMATICS")
    STATISTICS = _("STATISTICS")
    BIOLOGY = _("BIOLOGY")
    GEOGRAPHY = _("GEOGRAPHY")


CHOIX_COMMISSION_PROXIMITE = {
    choix.name: choix.value
    for choix in itertools.chain(
        ChoixCommissionProximiteCDEouCLSM,
        ChoixCommissionProximiteCDSS,
        ChoixSousDomaineSciences,
    )
}


class ChoixEtapeParcoursDoctoral(ChoiceEnum):
    ADMISSION = _('ADMISSION')
    JURY = _('JURY')
    CONFIRMATION = _('CONFIRMATION')
    DECISION_DE_RECEVABILITE = _('DECISION_DE_RECEVABILITE')
    DEFENSE_PRIVEE = _('DEFENSE_PRIVEE')
    SOUTENANCE_PUBLIQUE = _('SOUTENANCE_PUBLIQUE')
    ABANDON_ECHEC = _('ABANDON_ECHEC')


STATUTS_PAR_ETAPE_PARCOURS_DOCTORAL = {
    ChoixEtapeParcoursDoctoral.CONFIRMATION: [
        ChoixStatutParcoursDoctoral.ADMIS,
        ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE,
        ChoixStatutParcoursDoctoral.CONFIRMATION_A_REPRESENTER,
        ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE,
        ChoixStatutParcoursDoctoral.NON_AUTORISE_A_POURSUIVRE,
    ],
    ChoixEtapeParcoursDoctoral.JURY: [
        ChoixStatutParcoursDoctoral.JURY_SOUMIS,
        ChoixStatutParcoursDoctoral.JURY_APPROUVE_CA,
        ChoixStatutParcoursDoctoral.JURY_APPROUVE_CDD,
        ChoixStatutParcoursDoctoral.JURY_REFUSE_CDD,
        ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE,
        ChoixStatutParcoursDoctoral.JURY_REFUSE_ADRE,
    ],
    ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE: [],
    ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE: [],
    ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE: [],
    ChoixEtapeParcoursDoctoral.ABANDON_ECHEC: [
        ChoixStatutParcoursDoctoral.ABANDON,
    ],
}

STATUTS_INACTIFS = {ChoixStatutParcoursDoctoral.ABANDON.name}

STATUTS_ACTIFS = {choix.name for choix in ChoixStatutParcoursDoctoral if choix.name not in STATUTS_INACTIFS}
