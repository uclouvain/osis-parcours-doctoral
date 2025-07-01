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
from django.utils.translation import pgettext_lazy

from osis_common.ddd.interface import BusinessException


class NotEnoughMembersException(BusinessException):
    status_code = "JURY-1"

    def __init__(self, **kwargs):
        message = _("Your jury must have at least 5 members.")
        super().__init__(message, **kwargs)


class DefenseMethodNotCompletedException(BusinessException):
    status_code = "JURY-2"

    def __init__(self, **kwargs):
        message = _("Please input all required information from the \"Defense Method\" tab before requesting the signatures.")
        super().__init__(message, **kwargs)


class NoExternalMemberException(BusinessException):
    status_code = "JURY-3"

    def __init__(self, **kwargs):
        message = _("The jury must have at least one member from another institute than the UCLouvain, chosen depending on their particular expertise about the subject of the thesis.")
        super().__init__(message, **kwargs)
