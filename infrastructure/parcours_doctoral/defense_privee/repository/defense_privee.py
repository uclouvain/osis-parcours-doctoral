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

from parcours_doctoral.ddd.defense_privee.domain.model.defense_privee import (
    DefensePrivee,
    DefensePriveeIdentity,
)
from parcours_doctoral.ddd.defense_privee.dtos import DefensePriveeDTO
from parcours_doctoral.ddd.defense_privee.repository.i_defense_privee import (
    IDefensePriveeRepository,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.models import ParcoursDoctoral
from parcours_doctoral.models.private_defense import PrivateDefense


class DefensePriveeRepository(IDefensePriveeRepository):
    @classmethod
    def search_dto(
        cls,
        parcours_doctoral_id: Optional[ParcoursDoctoralIdentity] = None,
        entity_id: Optional['DefensePriveeIdentity'] = None,
        seulement_active: bool = False,
    ) -> List['DefensePriveeDTO']:
        qs = PrivateDefense.objects.annotate(
            doctorate_uuid=F('parcours_doctoral__uuid'),
            thesis_title=F('parcours_doctoral__thesis_proposed_title'),
        )

        if parcours_doctoral_id:
            qs = qs.filter(parcours_doctoral__uuid=parcours_doctoral_id.uuid)

        if seulement_active:
            qs = qs.filter(current_parcours_doctoral_id=F('parcours_doctoral_id'))

        if entity_id:
            qs = qs.filter(uuid=entity_id.uuid)

        if entity_id or (parcours_doctoral_id and seulement_active):
            qs = qs[:1]

        return [
            DefensePriveeDTO(
                uuid=str(private_defense.uuid),
                parcours_doctoral_uuid=str(private_defense.doctorate_uuid),  # From annotation
                titre_these=private_defense.thesis_title,  # From annotation
                est_active=bool(private_defense.current_parcours_doctoral_id),
                date_heure=private_defense.datetime,
                lieu=private_defense.place,
                date_envoi_manuscrit=private_defense.manuscript_submission_date,
                proces_verbal=private_defense.minutes,
                canevas_proces_verbal=private_defense.minutes_canvas,
            )
            for private_defense in qs
        ]

    @classmethod
    def save(cls, entity: 'DefensePrivee') -> 'DefensePriveeIdentity':
        doctorate_id = ParcoursDoctoral.objects.only('pk').get(uuid=entity.parcours_doctoral_id.uuid).pk

        private_defense, created = PrivateDefense.objects.update_or_create(
            uuid=entity.entity_id.uuid,
            parcours_doctoral_id=doctorate_id,
            defaults={
                'current_parcours_doctoral_id': doctorate_id if entity.est_active else None,
                'datetime': entity.date_heure,
                'place': entity.lieu,
                'manuscript_submission_date': entity.date_envoi_manuscrit,
                'minutes': entity.proces_verbal,
                'minutes_canvas': entity.canevas_proces_verbal,
            },
        )

        return entity.entity_id
