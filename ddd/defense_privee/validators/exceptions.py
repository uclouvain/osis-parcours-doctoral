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

from django.utils.translation import gettext_lazy as _

from osis_common.ddd.interface import BusinessException
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral


class DefensePriveeNonTrouveeException(BusinessException):
    status_code = 'DEFENSE-PRIVEE-1'

    def __init__(self, **kwargs):
        message = _('Private defense not found.')
        super().__init__(message, **kwargs)


class DefensePriveeNonCompleteeException(BusinessException):
    status_code = 'DEFENSE-PRIVEE-2'

    def __init__(self, **kwargs):
        message = _('Private defense not completed.')
        super().__init__(message, **kwargs)


class DefensePriveeNonActiveeException(BusinessException):
    status_code = 'DEFENSE-PRIVEE-3'

    def __init__(self, **kwargs):
        message = _('Private defense not activated.')
        super().__init__(message, **kwargs)


class StatutDoctoratDifferentDefensePriveeSoumiseException(BusinessException):
    status_code = 'DEFENSE-PRIVEE-4'

    def __init__(self, **kwargs):
        message = _("The doctorate must be in the status '%(status)s' to realize this action.") % {
            'status': ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE.value,
        }
        super().__init__(message, **kwargs)


class StatutDoctoratDifferentDefensePriveeAutoriseeException(BusinessException):
    status_code = 'DEFENSE-PRIVEE-5'

    def __init__(self, **kwargs):
        message = _("The doctorate must be in the status '%(status)s' to realize this action.") % {
            'status': ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_AUTORISEE.value,
        }
        super().__init__(message, **kwargs)
