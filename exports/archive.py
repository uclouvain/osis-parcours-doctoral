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
from django.conf import settings
from django.utils import translation

from base.models.person import Person
from parcours_doctoral.ddd.domain.model.document import TypeDocument
from parcours_doctoral.ddd.dtos import ParcoursDoctoralDTO
from parcours_doctoral.exports.utils import parcours_doctoral_generate_pdf
from parcours_doctoral.models import Document, ParcoursDoctoral


def doctorate_archive(doctorate: ParcoursDoctoral, doctorate_dto: ParcoursDoctoralDTO, author: Person = None):
    """
    Generate the archive of a doctorate
    :param doctorate: The doctorate object
    :param doctorate_dto: The doctorate dto
    :param author:
    :return: The document UUID
    """
    with translation.override(language=settings.LANGUAGE_CODE_FR):
        # Generate the pdf
        save_token = parcours_doctoral_generate_pdf(
            parcours_doctoral=doctorate_dto,
            template='parcours_doctoral/exports/archive.html',
            filename=f'archive_{doctorate_dto.reference}.pdf',
        )

        new_archive = Document(
            name='Archive',
            updated_by=author,
            file=[save_token],
            related_doctorate=doctorate,
            document_type=TypeDocument.SYSTEME.name,
        )

        new_archive.save()

        return new_archive.uuid
