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
import datetime
from typing import Dict, List, Optional, Tuple

from base.ddd.utils.in_memory_repository import InMemoryGenericRepository
from parcours_doctoral.ddd.formation.domain.model.enums import StatutActivite
from parcours_doctoral.ddd.formation.domain.model.evaluation import Evaluation
from parcours_doctoral.ddd.formation.domain.model.inscription_evaluation import (
    InscriptionEvaluationIdentity,
)
from parcours_doctoral.ddd.formation.domain.validator.exceptions import (
    EvaluationNonTrouveeException,
)
from parcours_doctoral.ddd.formation.dtos.evaluation import EvaluationDTO
from parcours_doctoral.ddd.formation.repository.i_evaluation import (
    IEvaluationRepository,
)


class EvaluationInMemoryRepository(InMemoryGenericRepository, IEvaluationRepository):
    entities: List['Evaluation']
    dates_defenses_privees: Dict[str, datetime.date] = {}
    periodes_encodage: Dict[int, Dict[int, Tuple[datetime.date, datetime.date]]] = {}

    @classmethod
    def _get_dto_from_domain_object(
        cls,
        enrollment: Evaluation,
    ) -> EvaluationDTO:
        periode_encodage = cls.get_periode_encodage_notes(
            annee=enrollment.entity_id.annee,
            session=enrollment.entity_id.session,
        )
        date_defense_privee = cls.dates_defenses_privees.get(enrollment.uuid)
        date_limite_encodage = cls.get_echeance_encodage_enseignant(
            date_defense_privee=date_defense_privee,
            periode_encodage=periode_encodage,
        )
        return EvaluationDTO(
            uuid=str(enrollment.uuid),
            note_soumise=enrollment.note_soumise,
            note_corrigee=enrollment.note_corrigee,
            echeance_enseignant=date_limite_encodage,
            uuid_activite='',
            session=enrollment.entity_id.session,
            est_inscrit_tardivement=False,
            code_unite_enseignement=enrollment.entity_id.code_unite_enseignement,
            annee=enrollment.entity_id.annee,
            statut=StatutActivite.ACCEPTEE.name,
            noma=enrollment.entity_id.noma,
            est_desinscrit_tardivement=False,
            sigle_formation='',
            periode_encodage_session=periode_encodage,
        )

    @classmethod
    def get_dto(cls, inscription_id: 'InscriptionEvaluationIdentity') -> EvaluationDTO:
        entity = next((entity for entity in cls.entities if entity.uuid == inscription_id.uuid), None)

        if not entity:
            raise EvaluationNonTrouveeException

        return cls._get_dto_from_domain_object(entity)

    @classmethod
    def search(cls, **kwargs) -> List[Evaluation]:
        return cls.entities

    @classmethod
    def search_dto(
        cls,
        annee: int,
        session: int,
        codes_unite_enseignement: List[str],
    ) -> List[EvaluationDTO]:
        return [
            cls._get_dto_from_domain_object(entity)
            for entity in cls.search(
                annee=annee,
                session=session,
                codes_unite_enseignement=codes_unite_enseignement,
            )
        ]

    @classmethod
    def get_periode_encodage_notes(
        cls,
        annee: int,
        session: int,
    ) -> Optional[tuple[datetime.date]]:
        return cls.periodes_encodage.get(annee, {}).get(session)
