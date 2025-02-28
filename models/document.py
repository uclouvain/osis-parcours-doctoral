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
import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _
from osis_document.contrib.fields import FileField

from parcours_doctoral.ddd.domain.model.document import TypeDocument

__all__ = [
    'Document',
]


def document_directory_path(document: 'Document', filename: str):
    """Return the file upload directory path."""
    return 'parcours_doctoral/{}/{}/{}'.format(
        document.related_doctorate.student.uuid,
        document.related_doctorate.uuid,
        filename,
    )


class Document(models.Model):
    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('UUID'),
    )

    name = models.CharField(
        max_length=255,
        null=False,
        verbose_name=_('Name'),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        null=False,
        verbose_name=_('Updated at'),
    )

    updated_by = models.ForeignKey(
        to='base.Person',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Updated by'),
        related_name='+',
    )

    file = FileField(
        upload_to=document_directory_path,
        verbose_name=_('File'),
        max_files=1,
        mimetypes=['application/pdf'],
    )

    related_doctorate = models.ForeignKey(
        to='parcours_doctoral.ParcoursDoctoral',
        on_delete=models.CASCADE,
        null=False,
        verbose_name=_('Related doctorate'),
    )

    document_type = models.CharField(
        max_length=255,
        null=False,
        verbose_name=_('Document type'),
        choices=TypeDocument.choices(),
    )

    class Meta:
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')
