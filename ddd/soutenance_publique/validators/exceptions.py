##############################################################################
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
##############################################################################

from django.utils.translation import gettext as _

from osis_common.ddd.interface import BusinessException
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral


class SoutenancePubliqueNonCompleteeException(BusinessException):
    status_code = 'SOUTENANCE-PUBLIQUE-1'

    def __init__(self, **kwargs):
        message = _('Public defense not completed.')
        super().__init__(message, **kwargs)


class EtapeSoutenancePubliquePasEnCoursException(BusinessException):
    status_code = 'SOUTENANCE-PUBLIQUE-2'

    def __init__(self, **kwargs):
        message = _('The step related to the public defense is not in progress.')
        super().__init__(message, **kwargs)


class StatutDoctoratDifferentSoutenancePubliqueSoumiseException(BusinessException):
    status_code = 'SOUTENANCE-PUBLIQUE-3'

    def __init__(self, **kwargs):
        message = _("The doctorate must be in the status '%(status)s' to realize this action.") % {
            'status': ChoixStatutParcoursDoctoral.SOUTENANCE_PUBLIQUE_SOUMISE.value,
        }
        super().__init__(message, **kwargs)


class StatutDoctoratDifferentSoutenancePubliqueAutoriseeException(BusinessException):
    status_code = 'SOUTENANCE-PUBLIQUE-4'

    def __init__(self, **kwargs):
        message = _("The doctorate must be in the status '%(status)s' to realize this action.") % {
            'status': ChoixStatutParcoursDoctoral.SOUTENANCE_PUBLIQUE_AUTORISEE.value,
        }
        super().__init__(message, **kwargs)


class SoutenancePubliqueNonCompleteePourDecisionException(BusinessException):
    status_code = 'SOUTENANCE-PUBLIQUE-5'

    def __init__(self, **kwargs):
        message = _(
            'Please be sure that the date and time of the defence have been filled in and that '
            'the defence minutes have been submitted in the application.'
        )
        super().__init__(message, **kwargs)
