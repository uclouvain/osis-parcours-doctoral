# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from typing import List, Optional

from django.db.models import F

from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.recevabilite.domain.model.recevabilite import (
    Recevabilite,
    RecevabiliteIdentity,
)
from parcours_doctoral.ddd.recevabilite.dtos import RecevabiliteDTO
from parcours_doctoral.ddd.recevabilite.repository.i_recevabilite import (
    IRecevabiliteRepository,
)
from parcours_doctoral.models import ParcoursDoctoral
from parcours_doctoral.models.admissibility import Admissibility


class RecevabiliteRepository(IRecevabiliteRepository):
    @classmethod
    def search_dto(
        cls,
        parcours_doctoral_id: Optional[ParcoursDoctoralIdentity] = None,
        entity_id: Optional['RecevabiliteIdentity'] = None,
        seulement_active: bool = False,
    ) -> List['RecevabiliteDTO']:
        qs = Admissibility.objects.annotate(
            doctorate_uuid=F('parcours_doctoral__uuid'),
        )

        if parcours_doctoral_id:
            qs = qs.filter(parcours_doctoral__uuid=parcours_doctoral_id.uuid)

        if seulement_active:
            qs = qs.filter(current_parcours_doctoral_id=F('parcours_doctoral_id'))

        if entity_id:
            qs = qs.filter(uuid=entity_id.uuid)

        return [
            RecevabiliteDTO(
                uuid=str(admissibility.uuid),
                parcours_doctoral_uuid=str(admissibility.doctorate_uuid),  # From annotation
                est_active=bool(admissibility.current_parcours_doctoral_id),
                date_decision=admissibility.decision_date,
                date_envoi_manuscrit=admissibility.manuscript_submission_date,
                avis_jury=admissibility.thesis_exam_board_opinion,
                proces_verbal=admissibility.minutes,
                canevas_proces_verbal=admissibility.minutes_canvas,
            )
            for admissibility in qs
        ]

    @classmethod
    def save(cls, entity: 'Recevabilite') -> 'RecevabiliteIdentity':
        doctorate_id = ParcoursDoctoral.objects.only('pk').get(uuid=entity.parcours_doctoral_id.uuid).pk

        admissibility, created = Admissibility.objects.update_or_create(
            uuid=entity.entity_id.uuid,
            parcours_doctoral_id=doctorate_id,
            defaults={
                'current_parcours_doctoral_id': doctorate_id if entity.est_active else None,
                'decision_date': entity.date_decision,
                'thesis_exam_board_opinion': entity.avis_jury,
                'manuscript_submission_date': entity.date_envoi_manuscrit,
                'minutes': entity.proces_verbal,
                'minutes_canvas': entity.canevas_proces_verbal,
            },
        )

        return entity.entity_id
