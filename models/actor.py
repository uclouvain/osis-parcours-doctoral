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
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from osis_document_components.fields import FileField
from osis_signature.models import Actor, ActorManager

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


class ParcoursDoctoralSupervisionActorQuerySet(QuerySet):
    def bulk_create(
        self,
        objs,
        batch_size=None,
        ignore_conflicts=False,
        update_conflicts=False,
        update_fields=None,
        unique_fields=None,
    ):
        """
        Bulk creation of objects with multi-table inheritance is not implemented yet so we do a simple version here.
        Doesn't work if the FileField fields have data (the call to the 'save' method is necessary and not done here)).
        """

        if not objs:
            return objs

        Actor.objects.bulk_create(objs, batch_size=batch_size)

        for obj in objs:
            obj.actor_ptr_id = obj.id

        self._batched_insert(
            objs=objs,
            fields=ParcoursDoctoralSupervisionActor._meta.local_concrete_fields,
            batch_size=batch_size,
        )


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

    objects = ActorManager.from_queryset(ParcoursDoctoralSupervisionActorQuerySet)()
