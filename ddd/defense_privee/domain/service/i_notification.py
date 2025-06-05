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
from abc import abstractmethod

from osis_common.ddd import interface

from parcours_doctoral.ddd.defense_privee.domain.model.defense_privee import (
    DefensePrivee,
)


class INotification(interface.DomainService):
    @classmethod
    @abstractmethod
    def notifier_soumission(cls, defense_privee: DefensePrivee) -> None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def notifier_nouvelle_echeance(cls, defense_privee: DefensePrivee) -> None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def notifier_echec_defense(
        cls,
        defense_privee: DefensePrivee,
        sujet_notification_candidat,
        message_notification_candidat,
    ) -> None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def notifier_repassage_defense(
        cls,
        defense_privee: DefensePrivee,
        sujet_notification_candidat,
        message_notification_candidat,
    ) -> None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def notifier_reussite_defense(cls, defense_privee: DefensePrivee) -> None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def notifier_completion_par_promoteur(cls, defense_privee: DefensePrivee) -> None:
        raise NotImplementedError
