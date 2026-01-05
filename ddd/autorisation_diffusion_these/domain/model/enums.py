# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from base.models.utils.utils import ChoiceEnum


class TypeModalitesDiffusionThese(ChoiceEnum):
    ACCES_LIBRE = _('Free access (Internet)')
    ACCES_RESTREINT = _('Limited access (Intranet)')
    ACCES_INTERDIT = _('Forbidden access')
    ACCES_EMBARGO = _('Embargo access')


class RoleActeur(ChoiceEnum):
    PROMOTEUR = _('Supervisor')
    SCEB = _('SCEB')
    ADRE = _('ADRE')


class ChoixStatutAutorisationDiffusionThese(ChoiceEnum):
    DIFFUSION_NON_SOUMISE = _('Not submitted distribution')
    DIFFUSION_SOUMISE = _('Submitted distribution')
    DIFFUSION_VALIDEE_PROMOTEUR = _('Distribution validated by the supervisor')
    DIFFUSION_REFUSEE_PROMOTEUR = _('Distribution refused by the supervisor')
    DIFFUSION_VALIDEE_ADRE = _('Distribution validated by ADRE')
    DIFFUSION_REFUSEE_ADRE = _('Distribution refused by ADRE')
    DIFFUSION_VALIDEE_SCEB = _('Distribution validated by SCEB')
    DIFFUSION_REFUSEE_SCEB = _('Distribution refused by SCEB')


CHOIX_STATUTS_AUTORISATION_DIFFUSION_THESE_MODIFIABLE_PAR_DOCTORANT = {
    ChoixStatutAutorisationDiffusionThese.DIFFUSION_NON_SOUMISE.name,
    ChoixStatutAutorisationDiffusionThese.DIFFUSION_REFUSEE_PROMOTEUR.name,
    ChoixStatutAutorisationDiffusionThese.DIFFUSION_REFUSEE_ADRE.name,
    ChoixStatutAutorisationDiffusionThese.DIFFUSION_REFUSEE_SCEB.name,
}

CHOIX_STATUTS_AUTORISATION_DIFFUSION_THESE_MODIFIABLE_PAR_PROMOTEUR_REFERENCE = {
    ChoixStatutAutorisationDiffusionThese.DIFFUSION_SOUMISE.name,
}

CHOIX_STATUTS_AUTORISATION_DIFFUSION_THESE_MODIFIABLE_PAR_ADRE = {
    ChoixStatutAutorisationDiffusionThese.DIFFUSION_VALIDEE_PROMOTEUR.name,
}

CHOIX_STATUTS_AUTORISATION_DIFFUSION_THESE_MODIFIABLE_PAR_SCEB = {
    ChoixStatutAutorisationDiffusionThese.DIFFUSION_VALIDEE_ADRE.name,
}


class ChoixEtatSignature(ChoiceEnum):
    NOT_INVITED = _('NOT_INVITED')  # Pas encore envoyée au signataire
    INVITED = _('INVITED')  # Envoyée au signataire
    APPROVED = pgettext_lazy("admission decision", "Approved")  # Approuvée par le signataire
    DECLINED = pgettext_lazy("admission decision", "Denied")  # Refusée par le signataire
