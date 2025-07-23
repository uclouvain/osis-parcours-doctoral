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


class NotEnoughMembersException(BusinessException):
    status_code = "JURY-1"

    def __init__(self, **kwargs):
        from parcours_doctoral.ddd.jury.domain.validator._should_jury_avoir_assez_de_membres import \
            NOMBRE_MINIMUM_JURY_MEMBERS

        message = _("Your jury must have at least %s members.") % (NOMBRE_MINIMUM_JURY_MEMBERS,)
        super().__init__(message, **kwargs)


class MethodeDeDefenseNonCompleteeException(BusinessException):
    status_code = "JURY-2"

    def __init__(self, **kwargs):
        message = _(
            "Please input all required information from the \"Defense Method\" tab before requesting the signatures."
        )
        super().__init__(message, **kwargs)


class PasDeMembreExterneException(BusinessException):
    status_code = "JURY-3"

    def __init__(self, **kwargs):
        message = _(
            "The jury must have at least one member from another institute than the UCLouvain, chosen depending on their particular expertise about the subject of the thesis."
        )
        super().__init__(message, **kwargs)


class SignataireNonTrouveException(BusinessException):
    status_code = "JURY-4"

    def __init__(self, **kwargs):
        message = _("Member of jury not found.")
        super().__init__(message, **kwargs)


class SignataireDejaInviteException(BusinessException):
    status_code = "JURY-5"

    def __init__(self, **kwargs):  # pragma: no cover
        message = _("Member of jury already invited.")
        super().__init__(message, **kwargs)


class SignatairePasInviteException(BusinessException):
    status_code = "JURY-6"

    def __init__(self, **kwargs):
        message = _("Member of jury not invited.")
        super().__init__(message, **kwargs)
