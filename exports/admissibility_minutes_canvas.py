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

from django.utils import translation
from osis_document_components.enums import PostProcessingWanted
from osis_document_components.services import get_remote_token
from osis_document_components.utils import get_file_url

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.commands import RecupererParcoursDoctoralQuery
from parcours_doctoral.ddd.jury.commands import RecupererJuryQuery
from parcours_doctoral.ddd.jury.domain.model.enums import ROLES_MEMBRES_JURY, RoleJury
from parcours_doctoral.ddd.jury.dtos.jury import MembreJuryDTO
from parcours_doctoral.exports.utils import parcours_doctoral_generate_pdf
from parcours_doctoral.models.admissibility import Admissibility


def admissibility_minutes_canvas_url(doctorate_uuid, language):
    """For a doctorate uuid, create the admissibility minutes canvas, save it and return the file url."""
    with translation.override(language=language):
        jury_dto, doctorate_dto = message_bus_instance.invoke_multiple(
            [
                RecupererJuryQuery(uuid_jury=doctorate_uuid),
                RecupererParcoursDoctoralQuery(parcours_doctoral_uuid=doctorate_uuid),
            ]
        )

        current_admissibility = Admissibility.objects.get(current_parcours_doctoral__uuid=doctorate_uuid)

        jury_members: list[MembreJuryDTO] = []
        jury_members_by_role: dict[str, MembreJuryDTO] = {}

        for member in jury_dto.membres:
            jury_members_by_role[member.role] = member
            if member.role in ROLES_MEMBRES_JURY:
                jury_members.append(member)

        # Generate the pdf
        save_token = parcours_doctoral_generate_pdf(
            template='parcours_doctoral/exports/admissibility_minutes_canvas.html',
            filename=f'admissibility_minutes_canvas_{doctorate_dto.reference}.pdf',
            context={
                'parcours_doctoral': doctorate_dto,
                'jury_members': jury_members,
                'jury_president': jury_members_by_role.get(RoleJury.PRESIDENT.name),
                'jury_secretary': jury_members_by_role.get(RoleJury.SECRETAIRE.name),
                'admissibility_decision_date': current_admissibility.decision_date,
            },
        )

        # Attach the file to the object
        current_admissibility.minutes_canvas = [save_token]
        current_admissibility.save(update_fields=['minutes_canvas'])

        reading_token = get_remote_token(
            current_admissibility.minutes_canvas[0],
            wanted_post_process=PostProcessingWanted.ORIGINAL.name,
        )

        url = get_file_url(reading_token)

        return url
