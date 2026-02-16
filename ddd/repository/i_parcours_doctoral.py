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
import abc
from abc import ABCMeta
from typing import List

from osis_common.ddd import interface
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoral,
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.dtos import (
    CotutelleDTO,
    ParcoursDoctoralDTO,
    ParcoursDoctoralRechercheEtudiantDTO,
)

CAMPUS_LETTRE_DOSSIER = {
    'Bruxelles Saint-Louis': 'B',
    'Charleroi': 'C',
    'Louvain-la-Neuve': 'L',
    'Mons': 'M',
    'Namur': 'N',
    'Tournai': 'T',
    'Bruxelles Woluwe': 'W',
    'Bruxelles Saint-Gilles': 'G',
    'Autre site': 'X',
}


class IParcoursDoctoralRepository(interface.AbstractRepository, metaclass=ABCMeta):
    @classmethod
    @abc.abstractmethod
    def get(cls, entity_id: 'ParcoursDoctoralIdentity') -> 'ParcoursDoctoral':  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def verifier_existence(cls, entity_id: 'ParcoursDoctoralIdentity') -> None:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def save(cls, entity: 'ParcoursDoctoral') -> None:  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_dto(
        cls,
        entity_id: 'ParcoursDoctoralIdentity' = None,
        proposition_id: 'PropositionIdentity' = None,
    ) -> 'ParcoursDoctoralDTO':
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_cotutelle_dto(cls, entity_id: 'ParcoursDoctoralIdentity') -> 'CotutelleDTO':
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def search_dto(
        cls,
        matricule_doctorant: str = None,
        matricule_membre: str = None,
    ) -> List['ParcoursDoctoralRechercheEtudiantDTO']:
        raise NotImplementedError
