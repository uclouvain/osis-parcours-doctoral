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
from typing import Union

from parcours_doctoral.ddd.defense_privee.domain.model.defense_privee import (
    DefensePrivee,
)
from parcours_doctoral.ddd.defense_privee.domain.service.i_notification import (
    INotification,
)
from parcours_doctoral.ddd.defense_privee.dtos import DefensePriveeDTO
from parcours_doctoral.infrastructure.mixins.notification import NotificationMixin
from parcours_doctoral.models import ParcoursDoctoral
from parcours_doctoral.utils.url import (
    get_parcours_doctoral_link_back,
    get_parcours_doctoral_link_front,
)


class Notification(NotificationMixin, INotification):
    @classmethod
    def _get_doctorate(cls, doctorate_uuid):
        return ParcoursDoctoral.objects.select_related(
            'student',
            'training',
        ).get(uuid=doctorate_uuid)

    @classmethod
    def get_common_tokens(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        defense_privee: Union[DefensePrivee, DefensePriveeDTO],
    ) -> dict:
        '''Return common tokens about a parcours doctoral'''
        return {
            'student_first_name': parcours_doctoral.student.first_name,
            'student_last_name': parcours_doctoral.student.last_name,
            'training_title': cls._get_parcours_doctoral_title_translation(parcours_doctoral),
            'parcours_doctoral_link_front': get_parcours_doctoral_link_front(parcours_doctoral.uuid),
            'parcours_doctoral_link_back': get_parcours_doctoral_link_back(parcours_doctoral.uuid),
            'private_defense_link_front': get_parcours_doctoral_link_front(parcours_doctoral.uuid, 'private-defense'),
            'private_defense_link_back': get_parcours_doctoral_link_back(parcours_doctoral.uuid, 'private-defense'),
            'private_defense_datetime': cls._format_datetime(defense_privee.date_heure),
            'reference': parcours_doctoral.reference,
        }
