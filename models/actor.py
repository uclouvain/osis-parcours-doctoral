# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from osis_document.contrib import FileField
from osis_signature.models import Actor

from base.models.utils.utils import ChoiceEnum
from parcours_doctoral.models.parcours_doctoral import ParcoursDoctoral

__all__ = ['ActorType', 'ParcoursDoctoralSupervisionActor']


def actor_upload_directory_path(instance: 'ParcoursDoctoralSupervisionActor', filename):
    """Return the file upload directory path."""
    parcours_doctoral = ParcoursDoctoral.objects.select_related('student').get(
        supervision_group=instance.process,
    )
    return 'parcours_doctoral/{}/{}/approvals/{}'.format(
        parcours_doctoral.student.uuid,
        parcours_doctoral.uuid,
        filename,
    )


class ActorType(ChoiceEnum):
    PROMOTER = _("Supervisor")
    CA_MEMBER = _("CA Member")


class ParcoursDoctoralSupervisionActor(Actor):
    """This model extends Actor from OSIS-Signature"""

    type = models.CharField(
        choices=ActorType.choices(),
        max_length=50,
    )
    is_doctor = models.BooleanField(
        default=False,
    )
    internal_comment = models.TextField(
        default='',
        verbose_name=_('Internal comment'),
        blank=True,
    )
    pdf_from_candidate = FileField(
        min_files=1,
        max_files=1,
        mimetypes=['application/pdf'],
        verbose_name=_("PDF file"),
        upload_to=actor_upload_directory_path,
    )
    is_reference_promoter = models.BooleanField(
        default=False,
    )

    @property
    def complete_name(self):
        return f'{self.last_name}, {self.first_name}'
