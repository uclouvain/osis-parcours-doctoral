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
        from parcours_doctoral.ddd.jury.domain.validator._should_jury_avoir_assez_de_membres import (
            NOMBRE_MINIMUM_JURY_MEMBERS,
        )

        message = _("Your jury must have at least %s members.") % (NOMBRE_MINIMUM_JURY_MEMBERS,)
        super().__init__(message, **kwargs)


class MethodeDeDefenseNonCompleteeException(BusinessException):
    status_code = "JURY-2"

    def __init__(self, **kwargs):
        message = _(
            "Please input all required information from the \"Defence Method\" tab before requesting the signatures."
        )
        super().__init__(message, **kwargs)


class PasDeMembreExterneException(BusinessException):
    status_code = "JURY-3"

    def __init__(self, **kwargs):
        message = _(
            "The jury must have at least one member from another institute than the UCLouvain, chosen depending on "
            "their particular expertise about the subject of the thesis."
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


class PromoteurPresidentException(BusinessException):
    status_code = "JURY-7"

    def __init__(self, **kwargs):
        message = _("A supervisor can not be president.")
        super().__init__(message, **kwargs)


class MembreNonTrouveDansJuryException(BusinessException):
    status_code = "JURY-8"

    def __init__(self, uuid_membre, jury, **kwargs):
        self.uuid_membre = uuid_membre
        self.jury = jury
        message = _("The member was not found in the jury.")
        super().__init__(message, **kwargs)


class JuryNonTrouveException(BusinessException):
    status_code = "JURY-9"

    def __init__(self, **kwargs):
        message = _("No jury found.")
        super().__init__(message, **kwargs)


class PromoteurRetireException(BusinessException):
    status_code = "JURY-10"

    def __init__(self, uuid_membre, jury, **kwargs):
        self.uuid_membre = uuid_membre
        self.jury = jury
        message = _("A supervisor can not be removed from the jury.")
        super().__init__(message, **kwargs)


class PromoteurModifieException(BusinessException):
    status_code = "JURY-11"

    def __init__(self, uuid_membre, jury, **kwargs):
        self.uuid_membre = uuid_membre
        self.jury = jury
        message = _("A supervisor can not be updated from the jury.")
        super().__init__(message, **kwargs)


class NonDocteurSansJustificationException(BusinessException):
    status_code = "JURY-12"

    def __init__(self, **kwargs):
        message = _("A non doctor member must have a justification.")
        super().__init__(message, **kwargs)


class MembreExterneSansInstitutionException(BusinessException):
    status_code = "JURY-13"

    def __init__(self, **kwargs):
        message = _("An external member must have an institute.")
        super().__init__(message, **kwargs)


class MembreExterneSansPaysException(BusinessException):
    status_code = "JURY-14"

    def __init__(self, **kwargs):
        message = _("An external member must have a country.")
        super().__init__(message, **kwargs)


class MembreExterneSansNomException(BusinessException):
    status_code = "JURY-15"

    def __init__(self, **kwargs):
        message = _("An external member must have a last name.")
        super().__init__(message, **kwargs)


class MembreExterneSansPrenomException(BusinessException):
    status_code = "JURY-16"

    def __init__(self, **kwargs):
        message = _("An external member must have a first name.")
        super().__init__(message, **kwargs)


class MembreExterneSansTitreException(BusinessException):
    status_code = "JURY-17"

    def __init__(self, **kwargs):
        message = _("An external member must have a title.")
        super().__init__(message, **kwargs)


class MembreExterneSansGenreException(BusinessException):
    status_code = "JURY-18"

    def __init__(self, **kwargs):
        message = _("An external member must have a gender.")
        super().__init__(message, **kwargs)


class MembreExterneSansEmailException(BusinessException):
    status_code = "JURY-19"

    def __init__(self, **kwargs):
        message = _("An external member must have an email.")
        super().__init__(message, **kwargs)


class MembreDejaDansJuryException(BusinessException):
    status_code = "JURY-20"

    def __init__(self, uuid_membre, jury, **kwargs):
        self.uuid_membre = uuid_membre
        self.jury = jury
        message = _("The member is already in the jury.")
        super().__init__(message, **kwargs)


class PasDeVerificateurException(BusinessException):
    status_code = "JURY-21"

    def __init__(self, **kwargs):
        message = _("No auditor are set for this training.")
        super().__init__(message, **kwargs)


class ModificationRoleImpossibleSSSException(BusinessException):
    status_code = "JURY-22"

    def __init__(self, **kwargs):
        message = _("Only the student can change jury roles for SSS doctorate.")
        super().__init__(message, **kwargs)


class ModificationRoleImpossibleSSHException(BusinessException):
    status_code = "JURY-23"

    def __init__(self, **kwargs):
        message = _("Only the lead supervisor can change jury roles for SSH doctorate.")
        super().__init__(message, **kwargs)


class ModificationRoleImpossibleSSTException(BusinessException):
    status_code = "JURY-24"

    def __init__(self, **kwargs):
        message = _("Only the auditor can change jury roles for SST doctorate.")
        super().__init__(message, **kwargs)


class RolesNonAttribueException(BusinessException):
    status_code = "JURY-25"

    def __init__(self, **kwargs):
        message = _("Please specify the president and secretary roles before submitting your approval.")
        super().__init__(message, **kwargs)


class AuteurNonCddException(BusinessException):
    status_code = "JURY-26"

    def __init__(self, **kwargs):
        message = _("Author of this command is not from the doctorate CDD.")
        super().__init__(message, **kwargs)


class AuteurNonAdreException(BusinessException):
    status_code = "JURY-27"

    def __init__(self, **kwargs):
        message = _("Author of this command is not a rector.")
        super().__init__(message, **kwargs)


class PasUnMembreException(BusinessException):
    status_code = "JURY-28"

    def __init__(self, **kwargs):
        message = _("The person is not a president, a secretary or a member.")
        super().__init__(message, **kwargs)


class MembreExterneSansLangueDeContactException(BusinessException):
    status_code = "JURY-29"

    def __init__(self, **kwargs):
        message = _("An external member must have a contact language.")
        super().__init__(message, **kwargs)


class TropDeRolesAttribuesException(BusinessException):
    status_code = "JURY-30"

    def __init__(self, **kwargs):
        message = _("There must be only one president and one secretary.")
        super().__init__(message, **kwargs)
