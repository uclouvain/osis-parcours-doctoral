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
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from osis_signature.contrib.fields import SignatureProcessField

from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral, ChoixLangueDefense, \
    ChoixTypeFinancement, ChoixDoctoratDejaRealise
from osis_document.contrib import FileField

from parcours_doctoral.ddd.jury.domain.model.enums import FormuleDefense


def parcours_doctoral_directory_path(parcours_doctoral: 'ParcoursDoctoral', filename: str):
    """Return the file upload directory path."""
    return 'parcours_doctoral/{}/{}/{}'.format(
        parcours_doctoral.candidate.uuid,
        parcours_doctoral.uuid,
        filename,
    )


class ParcoursDoctoral(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )

    created_at = models.DateTimeField(verbose_name=_('Created'), auto_now_add=True)
    modified_at = models.DateTimeField(verbose_name=_('Modified'), auto_now=True)

    candidate = models.ForeignKey(
        to="base.Person",
        verbose_name=_("Candidate"),
        related_name="%(class)ss",
        on_delete=models.PROTECT,
        editable=False,
    )

    training = models.ForeignKey(
        to="base.EducationGroupYear",
        verbose_name=pgettext_lazy("parcours_doctoral", "Course"),
        related_name="+",
        on_delete=models.CASCADE,
    )

    status = models.CharField(
        choices=ChoixStatutParcoursDoctoral.choices(),
        max_length=30,
        default=ChoixStatutParcoursDoctoral.ADMITTED.name,
        verbose_name=_("Post-enrolment status"),
    )

    # Projet
    project_title = models.CharField(
        max_length=1023,
        verbose_name=_("Project title"),
        default='',
        blank=True,
    )
    project_abstract = models.TextField(
        verbose_name=_("Abstract"),
        default='',
        blank=True,
    )
    thesis_language = models.ForeignKey(
        'reference.Language',
        on_delete=models.PROTECT,
        verbose_name=_("Thesis language"),
        null=True,
        blank=True,
    )
    thesis_institute = models.ForeignKey(
        'base.EntityVersion',
        related_name="+",
        verbose_name=_("Thesis institute"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    thesis_location = models.CharField(
        max_length=255,
        verbose_name=_("Thesis location"),
        default='',
        blank=True,
    )
    phd_alread_started = models.BooleanField(
        verbose_name=_("Has your PhD project already started?"),
        null=True,
        blank=True,
    )
    phd_alread_started_institute = models.CharField(
        max_length=255,
        verbose_name=_("Institution"),
        default='',
        blank=True,
    )
    work_start_date = models.DateField(
        verbose_name=_("Work start date"),
        null=True,
        blank=True,
    )
    project_document = FileField(
        verbose_name=_("Project"),
        upload_to=parcours_doctoral_directory_path,
    )
    gantt_graph = FileField(
        verbose_name=_("Gantt chart"),
        upload_to=parcours_doctoral_directory_path,
    )
    program_proposition = FileField(
        verbose_name=_("Program proposition"),
        upload_to=parcours_doctoral_directory_path,
    )
    additional_training_project = FileField(
        verbose_name=_("Complementary training proposition"),
        upload_to=parcours_doctoral_directory_path,
    )
    recommendation_letters = FileField(
        verbose_name=_("Letters of recommendation"),
        upload_to=parcours_doctoral_directory_path,
    )

    # Experience précédente de recherche
    phd_already_done = models.CharField(
        max_length=255,
        choices=ChoixDoctoratDejaRealise.choices(),
        verbose_name=_("PhD already done"),
        default=ChoixDoctoratDejaRealise.NO.name,
        blank=True,
    )
    phd_already_done_institution = models.CharField(
        max_length=255,
        verbose_name=_("Institution"),
        default='',
        blank=True,
    )
    phd_already_done_thesis_domain = models.CharField(
        max_length=255,
        verbose_name=_("Thesis field"),
        default='',
        blank=True,
    )
    phd_already_done_defense_date = models.DateField(
        verbose_name=_("Defense"),
        null=True,
        blank=True,
    )
    phd_already_done_no_defense_reason = models.CharField(
        max_length=255,
        verbose_name=_("No defense reason"),
        default='',
        blank=True,
    )

    # Cotutelle

    cotutelle = models.BooleanField()
    cotutelle_motivation = models.CharField(
        max_length=255,
        verbose_name=_("Motivation"),
        default='',
        blank=True,
    )
    cotutelle_institution_fwb = models.BooleanField(
        verbose_name=_("Institution Federation Wallonie-Bruxelles"),
        blank=True,
        null=True,
    )
    cotutelle_institution = models.UUIDField(
        verbose_name=_("Institution"),
        default=None,
        null=True,
        blank=True,
    )
    cotutelle_other_institution_name = models.CharField(
        max_length=255,
        verbose_name=_("Other institution name"),
        default='',
        blank=True,
    )
    cotutelle_other_institution_address = models.CharField(
        max_length=255,
        verbose_name=_("Other institution address"),
        default='',
        blank=True,
    )
    cotutelle_opening_request = FileField(
        verbose_name=_("Cotutelle request document"),
        max_files=1,
        upload_to=parcours_doctoral_directory_path,
    )
    cotutelle_convention = FileField(
        verbose_name=_("Joint supervision agreement"),
        max_files=1,
        upload_to=parcours_doctoral_directory_path,
    )
    cotutelle_other_documents = FileField(
        verbose_name=_("Other cotutelle-related documents"),
        upload_to=parcours_doctoral_directory_path,
    )

    # Jury
    thesis_proposed_title = models.CharField(
        max_length=255,
        verbose_name=_("Proposed thesis title"),
        default='',
        blank=True,
    )
    defense_method = models.CharField(
        max_length=255,
        verbose_name=_("Defense method"),
        choices=FormuleDefense.choices(),
        default='',
        blank=True,
    )
    defense_indicative_date = models.DateField(
        verbose_name=_("Defense indicative date"),
        null=True,
        blank=True,
    )
    defense_language = models.CharField(
        max_length=255,
        verbose_name=_("Defense language"),
        choices=ChoixLangueDefense.choices(),
        default=ChoixLangueDefense.UNDECIDED.name,
        blank=True,
    )
    comment_about_jury = models.TextField(
        default="",
        verbose_name=_("Comment about jury"),
        blank=True,
    )
    accounting_situation = models.BooleanField(
        null=True,
        blank=True,
    )
    jury_approval = FileField(
        verbose_name=_("Jury approval"),
        upload_to=parcours_doctoral_directory_path,
    )

    # Financement (for confirmation paper)
    financing_type = models.CharField(
        max_length=255,
        verbose_name=_("Funding type"),
        choices=ChoixTypeFinancement.choices(),
        default='',
        blank=True,
    )
    other_international_scholarship = models.CharField(
        max_length=255,
        verbose_name=_("Other international scholarship"),
        default='',
        blank=True,
    )
    international_scholarship = models.ForeignKey(
        to="admission.Scholarship",
        verbose_name=_("International scholarship"),
        related_name="+",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    # Supervision
    supervision_group = SignatureProcessField()

    class Meta:
        verbose_name = _("Doctorate admission")
        ordering = ('-created_at',)
        permissions = [
            ('download_jury_approved_pdf', _("Can download jury-approved PDF")),
            ('upload_jury_approved_pdf', _("Can upload jury-approved PDF")),
            ('validate_registration', _("Can validate registration")),
            ('approve_jury', _("Can approve jury")),
            ('approve_confirmation_paper', _("Can approve confirmation paper")),
            ('validate_doctoral_training', _("Can validate doctoral training")),
            ('view_admission_jury', _("Can view the information related to the admission jury")),
            ('change_admission_jury', _("Can update the information related to the admission jury")),
            ('view_admission_confirmation', _("Can view the information related to the confirmation paper")),
            (
                'change_admission_confirmation',
                _("Can update the information related to the confirmation paper"),
            ),
        ]
