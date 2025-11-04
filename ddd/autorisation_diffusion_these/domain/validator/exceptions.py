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


class SourcesFinancementsNonCompleteesException(BusinessException):
    status_code = "AUTORISATION-DIFFUSION-THESE-1"

    def __init__(self, **kwargs):
        message = _('The sources of funding must be specified.')
        super().__init__(message=message, **kwargs)


class ResumeAnglaisNonCompleteException(BusinessException):
    status_code = "AUTORISATION-DIFFUSION-THESE-2"

    def __init__(self, **kwargs):
        message = _('The summary in english must be specified.')
        super().__init__(message=message, **kwargs)


class LangueRedactionTheseNonCompleteeException(BusinessException):
    status_code = "AUTORISATION-DIFFUSION-THESE-3"

    def __init__(self, **kwargs):
        message = _('The thesis language must be specified.')
        super().__init__(message=message, **kwargs)


class MotsClesNonCompletesException(BusinessException):
    status_code = "AUTORISATION-DIFFUSION-THESE-4"

    def __init__(self, **kwargs):
        message = _('At least one keyword must be specified.')
        super().__init__(message=message, **kwargs)


class TypeModalitesDiffusionNonCompleteException(BusinessException):
    status_code = "AUTORISATION-DIFFUSION-THESE-5"

    def __init__(self, **kwargs):
        message = _('The distribution conditions type must be specified.')
        super().__init__(message=message, **kwargs)


class DateEmbargoModalitesDiffusionNonCompleteeException(BusinessException):
    status_code = "AUTORISATION-DIFFUSION-THESE-6"

    def __init__(self, **kwargs):
        message = _('The embargo date must be specified.')
        super().__init__(message=message, **kwargs)


class ModalitesDiffusionNonAccepteesException(BusinessException):
    status_code = "AUTORISATION-DIFFUSION-THESE-7"

    def __init__(self, **kwargs):
        message = _('The distributions conditions must be accepted.')
        super().__init__(message=message, **kwargs)


class AutorisationDiffusionTheseNonTrouveException(BusinessException):
    status_code = "AUTORISATION-DIFFUSION-THESE-8"

    def __init__(self, **kwargs):
        message = _('The distribution authorization has not been found.')
        super().__init__(message=message, **kwargs)
