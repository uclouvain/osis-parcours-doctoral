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
from django.db.models import F
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from osis_document_components.fields import FileField

__all__ = [
    'Admissibility',
]


def admissibility_directory_path(admissibility, filename: str):
    """Return the file upload directory path."""
    return 'parcours_doctoral/{}/{}/admissibility/{}/{}'.format(
        admissibility.parcours_doctoral.student.uuid,
        admissibility.parcours_doctoral.uuid,
        admissibility.uuid,
        filename,
    )


class Admissibility(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )

    created_at = models.DateTimeField(
        verbose_name=pgettext_lazy('admissibility', 'Created at'),
        auto_now_add=True,
    )

    current_parcours_doctoral = models.OneToOneField(
        'parcours_doctoral.ParcoursDoctoral',
        verbose_name=_('Doctorate whose this admissibility is the active one'),
        null=True,
        blank=True,
        related_name='current_admissibility',
        on_delete=models.CASCADE,
    )

    parcours_doctoral = models.ForeignKey(
        'parcours_doctoral.ParcoursDoctoral',
        verbose_name=_('Doctorate'),
        on_delete=models.CASCADE,
    )

    decision_date = models.DateField(
        verbose_name=_('Date of admissibility decision'),
        null=True,
        blank=True,
    )

    manuscript_submission_date = models.DateField(
        verbose_name=_('Date of manuscript submission to the thesis exam board'),
        null=True,
        blank=True,
    )

    thesis_exam_board_opinion = FileField(
        verbose_name=_('Thesis exam board opinion'),
        upload_to=admissibility_directory_path,
    )

    minutes = FileField(
        verbose_name=_('Admissibility minutes'),
        upload_to=admissibility_directory_path,
    )

    minutes_canvas = FileField(
        verbose_name=_('Admissibility minutes canvas'),
        upload_to=admissibility_directory_path,
    )

    class Meta:
        ordering = ['-created_at']
