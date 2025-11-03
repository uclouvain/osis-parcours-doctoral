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
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from osis_document_components.fields import FileField
from osis_signature.models import Actor

from parcours_doctoral.ddd.jury.domain.model.enums import (
    GenreMembre,
    RoleJury,
    TitreMembre,
)

__all__ = ['JuryActor']


def actor_upload_directory_path(instance: 'JuryActor', filename):
    """Return the file upload directory path."""
    from parcours_doctoral.models import ParcoursDoctoral

    parcours_doctoral = ParcoursDoctoral.objects.select_related('student').get(
        jury_group=instance.process,
    )
    return 'parcours_doctoral/{}/{}/jury/{}'.format(
        parcours_doctoral.student.uuid,
        parcours_doctoral.uuid,
        filename,
    )


class JuryActor(Actor):
    """This model extends Actor from OSIS-Signature"""

    is_promoter = models.BooleanField(
        verbose_name=_('Is a promoter'),
        default=False,
        blank=True,
    )
    is_lead_promoter = models.BooleanField(
        verbose_name=_('Is the lead promoter'),
        default=False,
        blank=True,
    )
    role = models.CharField(
        verbose_name=pgettext_lazy('jury', 'Role'),
        choices=RoleJury.choices(),
        max_length=50,
    )
    title = models.CharField(
        verbose_name=pgettext_lazy('admission', 'Title'),
        choices=TitreMembre.choices(),
        max_length=50,
        default='',
        blank=True,
    )
    non_doctor_reason = models.TextField(
        verbose_name=_('Non doctor reason'),
        max_length=255,
        default='',
        blank=True,
    )
    other_institute = models.CharField(
        verbose_name=_('Other institute'),
        max_length=255,
        default='',
        blank=True,
    )
    gender = models.CharField(
        verbose_name=_('Gender'),
        choices=GenreMembre.choices(),
        max_length=50,
    )
    internal_comment = models.TextField(
        default='',
        verbose_name=_('Internal comment'),
        blank=True,
    )
    rejection_reason = models.CharField(
        default='',
        max_length=50,
        blank=True,
        verbose_name=_('Grounds for denied'),
    )
    pdf_from_candidate = FileField(
        min_files=1,
        max_files=1,
        mimetypes=['application/pdf'],
        verbose_name=_("PDF file"),
        upload_to=actor_upload_directory_path,
    )

    @property
    def complete_name(self):
        return f'{self.last_name}, {self.first_name}'
