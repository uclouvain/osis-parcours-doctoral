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
from abc import abstractmethod
from email.message import EmailMessage

from osis_common.ddd import interface
from parcours_doctoral.ddd.domain.model.groupe_de_supervision import (
    GroupeDeSupervision,
    SignataireIdentity,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoral
from parcours_doctoral.ddd.jury.repository.i_jury import IJuryRepository


class INotification(interface.DomainService):
    @classmethod
    @abstractmethod
    def envoyer_message(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_emetteur: str,
        matricule_doctorant: str,
        sujet: str,
        message: str,
        cc_promoteurs: bool = False,
        cc_membres_ca: bool = False,
        cc_jury: bool = False,
        cc_sceb: bool = False,
    ) -> EmailMessage:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def envoyer_message_au_doctorant_et_au_jury(
        cls,
        jury_repository: IJuryRepository,
        parcours_doctoral: ParcoursDoctoral,
        sujet: str,
        message: str,
    ) -> EmailMessage:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def envoyer_signatures(
        cls, parcours_doctoral: ParcoursDoctoral, groupe_de_supervision: GroupeDeSupervision
    ) -> None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def renvoyer_invitation(cls, parcours_doctoral: ParcoursDoctoral, membre: SignataireIdentity):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def notifier_suppression_membre(
        cls, parcours_doctoral: ParcoursDoctoral, signataire_id: SignataireIdentity
    ) -> None:
        raise NotImplementedError
