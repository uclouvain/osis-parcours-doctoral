##############################################################################
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
##############################################################################

from django.utils.translation import gettext_lazy as _

from osis_common.ddd.interface import BusinessException


class ParcoursDoctoralNonTrouveException(BusinessException):
    status_code = "PARCOURS-DOCTORAL-1"

    def __init__(self, **kwargs):
        message = _("No parcours doctoral found.")
        super().__init__(message, **kwargs)


class PromoteurNonTrouveException(BusinessException):
    status_code = "PARCOURS-DOCTORAL-2"

    def __init__(self, **kwargs):
        message = _("Supervisor not found.")
        super().__init__(message, **kwargs)


class MembreCANonTrouveException(BusinessException):
    status_code = "PARCOURS-DOCTORAL-3"

    def __init__(self, **kwargs):
        message = _("Membre CA not found.")
        super().__init__(message, **kwargs)


class SignataireNonTrouveException(BusinessException):
    status_code = "PARCOURS-DOCTORAL-4"

    def __init__(self, **kwargs):
        message = _("Member of supervision group not found.")
        super().__init__(message, **kwargs)


class SignataireDejaInviteException(BusinessException):
    status_code = "PARCOURS-DOCTORAL-5"

    def __init__(self, **kwargs):  # pragma: no cover
        message = _("Member of supervision group already invited.")
        super().__init__(message, **kwargs)


class SignatairePasInviteException(BusinessException):
    status_code = "PARCOURS-DOCTORAL-6"

    def __init__(self, **kwargs):
        message = _("Member of supervision group not invited.")
        super().__init__(message, **kwargs)


class MembreSoitInterneSoitExterneException(BusinessException):
    status_code = "PARCOURS-DOCTORAL-7"

    def __init__(self, **kwargs):
        message = _("A member should be either internal or external, please check the fields.")
        super().__init__(message, **kwargs)


class DejaMembreException(BusinessException):
    status_code = "PARCOURS-DOCTORAL-8"

    def __init__(self, **kwargs):
        message = _("Already a member.")
        super().__init__(message, **kwargs)


class ProcedureDemandeSignatureNonLanceeException(BusinessException):
    status_code = "PARCOURS-DOCTORAL-9"

    def __init__(self, **kwargs):
        message = _("The signature request procedure isn't in progress.")
        super().__init__(message, **kwargs)


class PropositionNonApprouveeParPromoteurException(BusinessException):
    status_code = "PARCOURS-DOCTORAL-10"

    def __init__(self, **kwargs):
        message = _("All supervisors must have approved the proposition.")
        super().__init__(message, **kwargs)


class PropositionNonApprouveeParMembresCAException(BusinessException):
    status_code = "PARCOURS-DOCTORAL-11"

    def __init__(self, **kwargs):
        message = _("All CA members must have approved the proposition.")
        super().__init__(message, **kwargs)


class PromoteurManquantException(BusinessException):
    status_code = "PARCOURS-DOCTORAL-12"

    def __init__(self, **kwargs):
        message = _("You must add at least one UCLouvain supervisor in order to request signatures.")
        super().__init__(message, **kwargs)


class MembreCAManquantException(BusinessException):
    status_code = "PARCOURS-DOCTORAL-13"

    def __init__(self, **kwargs):
        message = _("You must add at least two CA member in order to request signatures.")
        super().__init__(message, **kwargs)


class ProcedureDemandeSignatureLanceeException(BusinessException):
    status_code = "PARCOURS-DOCTORAL-14"

    def __init__(self, **kwargs):
        message = _("The signature request procedure is already in progress.")
        super().__init__(message, **kwargs)


class PropositionNonEnAttenteDeSignatureException(BusinessException):
    status_code = "PARCOURS-DOCTORAL-15"

    def __init__(self, **kwargs):
        message = _("The proposition must be in the 'waiting for signature' status.")
        super().__init__(message, **kwargs)


class PromoteurDeReferenceManquantException(BusinessException):
    status_code = "PARCOURS-DOCTORAL-16"

    def __init__(self, **kwargs):
        message = _("You must set a lead supervisor.")
        super().__init__(message, **kwargs)


class GroupeSupervisionCompletPourPromoteursException(BusinessException):
    status_code = "PARCOURS-DOCTORAL-17"

    def __init__(self, **kwargs):
        message = _("There can be no more promoters in the supervision group.")
        super().__init__(message, **kwargs)


class GroupeSupervisionCompletPourMembresCAException(BusinessException):
    status_code = "PARCOURS-DOCTORAL-18"

    def __init__(self, **kwargs):
        message = _("There can be no more CA members in the supervision group.")
        super().__init__(message, **kwargs)


class GroupeDeSupervisionNonTrouveException(BusinessException):
    status_code = "PARCOURS-DOCTORAL-19"

    def __init__(self, **kwargs):
        message = _("Supervision group not found.")
        super().__init__(message, **kwargs)
