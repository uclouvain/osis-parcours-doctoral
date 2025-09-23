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
    'PrivateDefense',
]


def private_defense_directory_path(private_defense, filename: str):
    """Return the file upload directory path."""
    return 'parcours_doctoral/{}/{}/private_defense/{}/{}'.format(
        private_defense.parcours_doctoral.student.uuid,
        private_defense.parcours_doctoral.uuid,
        private_defense.uuid,
        filename,
    )


class PrivateDefenseQuerySet(models.QuerySet):
    def for_model_object(self):
        return self.annotate(
            doctorate_uuid=F('parcours_doctoral__uuid'),
        )

    def for_dto(self):
        return self.annotate(
            thesis_title=F('parcours_doctoral__thesis_proposed_title'),
        )


class PrivateDefense(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )

    created_at = models.DateTimeField(
        verbose_name=pgettext_lazy('private defense', 'Created at'),
        auto_now_add=True,
    )

    current_parcours_doctoral = models.OneToOneField(
        'parcours_doctoral.ParcoursDoctoral',
        verbose_name=_('Doctorate whose this private defense is the active one'),
        null=True,
        blank=True,
        related_name='current_private_defense',
        on_delete=models.CASCADE,
    )

    parcours_doctoral = models.ForeignKey(
        'parcours_doctoral.ParcoursDoctoral',
        verbose_name=_('Doctorate'),
        on_delete=models.CASCADE,
    )

    datetime = models.DateTimeField(
        verbose_name=_('Private defence date and time'),
        null=True,
        blank=True,
    )

    place = models.TextField(
        verbose_name=_('Private defence location'),
        blank=True,
        default='',
    )

    manuscript_submission_date = models.DateField(
        verbose_name=_('Date of manuscript submission to the thesis exam board'),
        null=True,
        blank=True,
    )

    minutes = FileField(
        verbose_name=_('Private defence minutes'),
        upload_to=private_defense_directory_path,
    )

    minutes_canvas = FileField(
        verbose_name=_('Private defence minutes canvas'),
        upload_to=private_defense_directory_path,
    )

    objects = models.Manager.from_queryset(PrivateDefenseQuerySet)()

    class Meta:
        ordering = ['-created_at']
