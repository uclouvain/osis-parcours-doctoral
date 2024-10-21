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
import itertools

from base.models.utils.utils import ChoiceEnum
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy


class ChoixStatutParcoursDoctoral(ChoiceEnum):
    # After enrolment
    ADMITTED = _('ADMITTED')
    # Groupe de supervision
    EN_ATTENTE_DE_SIGNATURE = _('Waiting for signature')
    # Confirmation exam
    SUBMITTED_CONFIRMATION = _('SUBMITTED_CONFIRMATION')
    PASSED_CONFIRMATION = _('PASSED_CONFIRMATION')
    NOT_ALLOWED_TO_CONTINUE = _('NOT_ALLOWED_TO_CONTINUE')
    CONFIRMATION_TO_BE_REPEATED = _('CONFIRMATION_TO_BE_REPEATED')
    # Jury
    JURY_SOUMIS = _('JURY_SOUMIS')
    JURY_APPROUVE_CA = _('JURY_APPROUVE_CA')
    JURY_APPROUVE_CDD = _('JURY_APPROUVE_CDD')
    JURY_REFUSE_CDD = _('JURY_REFUSE_CDD')
    JURY_APPROUVE_ADRE = _('JURY_APPROUVE_ADRE')
    JURY_REFUSE_ADRE = _('JURY_REFUSE_ADRE')


STATUTS_DOCTORAT_EPREUVE_CONFIRMATION_EN_COURS = {
    ChoixStatutParcoursDoctoral.ADMITTED.name,
    ChoixStatutParcoursDoctoral.SUBMITTED_CONFIRMATION.name,
    ChoixStatutParcoursDoctoral.CONFIRMATION_TO_BE_REPEATED.name,
}


class ChoixLangueDefense(ChoiceEnum):
    FRENCH = _('French')
    ENGLISH = _('English')
    OTHER = _('Other')
    UNDECIDED = _('Undecided')


class ChoixDoctoratDejaRealise(ChoiceEnum):
    YES = _('YES')
    NO = _('NO')
    PARTIAL = _('PARTIAL')


class ChoixTypeFinancement(ChoiceEnum):
    WORK_CONTRACT = _('WORK_CONTRACT')
    SEARCH_SCHOLARSHIP = _('SEARCH_SCHOLARSHIP')
    SELF_FUNDING = _('SELF_FUNDING')


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
    GIM = _("Proximity Commission for Genetics and Immunology (GIM)")
    NRSC = _("Proximity Commission for Neuroscience (NRSC)")
    BCM = _("Proximity commission for cellular and molecular biology, biochemistry (BCM)")
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
