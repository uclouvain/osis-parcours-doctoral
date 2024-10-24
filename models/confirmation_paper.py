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
import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _
from osis_document.contrib import FileField


def confirmation_paper_directory_path(confirmation, filename: str):
    """Return the file upload directory path."""
    return 'parcours_doctoral/{}/{}/confirmation/{}/{}'.format(
        confirmation.admission.candidate.uuid,
        confirmation.admission.uuid,
        confirmation.uuid,
        filename,
    )


class ConfirmationPaper(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )

    parcours_doctoral = models.ForeignKey(
        'parcours_doctoral.ParcoursDoctoral',
        verbose_name=_("Parcours doctoral"),
        on_delete=models.CASCADE,
    )

    confirmation_date = models.DateField(
        verbose_name=_("Confirmation exam date"),
        null=True,
        blank=True,
    )
    confirmation_deadline = models.DateField(
        verbose_name=_("Confirmation deadline"),
        blank=True,
    )
    research_report = FileField(
        verbose_name=_("Research report"),
        upload_to=confirmation_paper_directory_path,
        max_files=1,
    )
    supervisor_panel_report = FileField(
        verbose_name=_("Support Committee minutes"),
        upload_to=confirmation_paper_directory_path,
        max_files=1,
    )
    supervisor_panel_report_canvas = FileField(
        verbose_name=_("Canvas of the report of the supervisory panel"),
        upload_to=confirmation_paper_directory_path,
        max_files=1,
    )
    research_mandate_renewal_opinion = FileField(
        verbose_name=_("Opinion on research mandate renewal"),
        upload_to=confirmation_paper_directory_path,
        max_files=1,
    )

    # Result of the confirmation
    certificate_of_failure = FileField(
        verbose_name=_("Certificate of failure"),
        upload_to=confirmation_paper_directory_path,
    )
    certificate_of_achievement = FileField(
        verbose_name=_("Certificate of achievement"),
        upload_to=confirmation_paper_directory_path,
    )

    # Extension
    extended_deadline = models.DateField(
        verbose_name=_("Deadline extended"),
        null=True,
        blank=True,
    )
    cdd_opinion = models.TextField(
        default="",
        verbose_name=_("CDD opinion"),
        blank=True,
    )
    justification_letter = FileField(
        verbose_name=_("Justification letter"),
        upload_to=confirmation_paper_directory_path,
    )
    brief_justification = models.TextField(
        default="",
        verbose_name=_("Brief justification"),
        blank=True,
        max_length=2000,
    )

    class Meta:
        ordering = ["-id"]
