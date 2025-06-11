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
from typing import List

from parcours_doctoral.ddd.defense_privee.builder.defense_privee_identity import DefensePriveeIdentityBuilder
from parcours_doctoral.ddd.defense_privee.domain.model.defense_privee import DefensePriveeIdentity, DefensePrivee
from parcours_doctoral.ddd.defense_privee.dtos import DefensePriveeDTO
from parcours_doctoral.ddd.defense_privee.repository.i_defense_privee import IDefensePriveeRepository
from parcours_doctoral.ddd.defense_privee.validators.exceptions import DefensePriveeNonTrouveeException
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoralIdentity
from parcours_doctoral.models.private_defense import PrivateDefense


class DefensePriveeRepository(IDefensePriveeRepository):
    @classmethod
    def get(cls, entity_id: 'DefensePriveeIdentity', parcours_doctoral_uuid: str = '') -> 'DefensePrivee':
        try:
            qs = PrivateDefense.objects.for_model_object()

            if parcours_doctoral_uuid:
                qs = qs.filter(parcours_doctoral__uuid=parcours_doctoral_uuid)

            private_defense: PrivateDefense = qs.get(uuid=entity_id.uuid)
        except PrivateDefense.DoesNotExist:
            raise DefensePriveeNonTrouveeException

        return DefensePrivee(
            entity_id=entity_id,
            parcours_doctoral_id=private_defense.parcours_doctoral_uuid,  # From annotation
            titre_these=private_defense.thesis_title,  # From annotation
            est_active=private_defense.is_active,
            date_heure=private_defense.datetime,
            lieu=private_defense.place,
            date_envoi_manuscrit=private_defense.manuscript_submission_date,
            proces_verbal=private_defense.minutes,
            canevas_proces_verbal=private_defense.minutes_canvas,
        )

    @classmethod
    def get_dto(cls, entity_id: 'DefensePriveeIdentity', parcours_doctoral_uuid: str = '') -> 'DefensePriveeDTO':
        try:
            qs = PrivateDefense.objects.for_dto()

            if parcours_doctoral_uuid:
                qs = qs.filter(parcours_doctoral__uuid=parcours_doctoral_uuid)

            private_defense = qs.get(uuid=entity_id.uuid)
        except PrivateDefense.DoesNotExist:
            raise DefensePriveeNonTrouveeException

        return DefensePriveeRepository.build_dto_from_model(private_defense)

    @classmethod
    def build_dto_from_model(cls, private_defense: PrivateDefense):
        return DefensePriveeDTO(
            uuid=str(private_defense.uuid),
            titre_these=private_defense.thesis_title,  # From annotation
            est_active=private_defense.is_active,
            date_heure=private_defense.datetime,
            lieu=private_defense.place,
            date_envoi_manuscrit=private_defense.manuscript_submission_date,
            proces_verbal=private_defense.minutes,
            canevas_proces_verbal=private_defense.minutes_canvas,
        )

    @classmethod
    def search_dto_by_parcours_doctoral_identity(
        cls,
        parcours_doctoral_entity_id: 'ParcoursDoctoralIdentity',
    ) -> List['DefensePriveeDTO']:
        private_defenses = PrivateDefense.objects.for_dto().filter(
            parcours_doctoral__uuid=parcours_doctoral_entity_id.uuid
        )

        return [cls.build_dto_from_model(private_defense) for private_defense in private_defenses]

    @classmethod
    def get_active_dto_by_parcours_doctoral_identity(
        cls,
        parcours_doctoral_entity_id: 'ParcoursDoctoralIdentity',
    ) -> 'DefensePriveeDTO':
        pass

    @classmethod
    def get_active_identity_by_parcours_doctoral_identity(
        cls,
        parcours_doctoral_entity_id: 'ParcoursDoctoralIdentity',
    ) -> 'DefensePriveeIdentity':
        try:
            private_defense = PrivateDefense.objects.get(
                parcours_doctoral__uuid=parcours_doctoral_entity_id.uuid,
                active=True,
            ).only('uuid')
        except PrivateDefense.DoesNotExist:
            raise DefensePriveeNonTrouveeException

        return DefensePriveeIdentityBuilder.build_from_uuid(uuid=str(private_defense.uuid))

    @classmethod
    def save(cls, entity: 'DefensePrivee') -> 'DefensePriveeIdentity':
        private_defense, created = PrivateDefense.objects.update_or_create(
            uuid=entity.entity_id.uuid,
            defaults={
                'is_active': entity.est_active,
                'datetime': entity.date_heure,
                'place': entity.lieu,
                'manuscript_submission_date': entity.date_envoi_manuscrit,
                'minutes': entity.proces_verbal,
                'minutes_canvas': entity.canevas_proces_verbal,
            },
        )
        return entity.entity_id
