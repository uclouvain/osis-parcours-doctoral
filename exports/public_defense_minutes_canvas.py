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
from parcours_doctoral.ddd.jury.domain.model.enums import ROLES_MEMBRES_JURY
from parcours_doctoral.exports.utils import parcours_doctoral_generate_pdf
from parcours_doctoral.models import Activity, ParcoursDoctoral


def public_defense_minutes_canvas_url(doctorate_uuid, language):
    """For a doctorate uuid, create the public defence canvas, save it and return the file url."""
    with translation.override(language=language):
        jury_dto, doctorate_dto = message_bus_instance.invoke_multiple(
            [
                RecupererJuryQuery(uuid_jury=doctorate_uuid),
                RecupererParcoursDoctoralQuery(parcours_doctoral_uuid=doctorate_uuid),
            ]
        )

        has_additional_training = Activity.objects.has_complementary_training(parcours_doctoral_uuid=doctorate_uuid)

        # Generate the pdf
        save_token = parcours_doctoral_generate_pdf(
            template='parcours_doctoral/exports/public_defense_minutes_canvas.html',
            filename='public_defense_canvas.pdf',
            context={
                'parcours_doctoral': doctorate_dto,
                'jury_members': [member for member in jury_dto.membres if member.role in ROLES_MEMBRES_JURY],
                'has_additional_training': has_additional_training,
            },
        )

        # Attach the file to the object
        doctorate = ParcoursDoctoral.objects.get(uuid=doctorate_uuid)
        doctorate.defense_minutes_canvas = [save_token]
        doctorate.save(update_fields=['defense_minutes_canvas'])

        reading_token = get_remote_token(
            doctorate.defense_minutes_canvas[0],
            wanted_post_process=PostProcessingWanted.ORIGINAL.name,
        )

        url = get_file_url(reading_token)

        return url
