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

from django.core.cache import cache
from django.db import models
from django.db.models import Case, CharField, F, OuterRef, Q, Subquery, Value, When
from django.db.models.functions import Coalesce, Concat, JSONObject, Mod, Replace
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from osis_document.contrib import FileField
from osis_history.models import HistoryEntry
from osis_signature.contrib.fields import SignatureProcessField

from admission.models.functions import ToChar
from base.models.education_group_year import EducationGroupYear
from base.models.entity_version import EntityVersion
from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import TrainingType
from base.models.person import Person
from base.models.student import Student
from parcours_doctoral.ddd.domain.model.enums import (
    STATUTS_DOCTORAT_EN_COURS_DE_CREATION,
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixDoctoratDejaRealise,
    ChoixLangueDefense,
    ChoixSousDomaineSciences,
    ChoixStatutParcoursDoctoral,
    ChoixTypeFinancement,
)
from parcours_doctoral.ddd.jury.domain.model.enums import FormuleDefense
from parcours_doctoral.ddd.repository.i_parcours_doctoral import CAMPUS_LETTRE_DOSSIER
from program_management.models.education_group_version import EducationGroupVersion

__all__ = [
    'ParcoursDoctoral',
]


def parcours_doctoral_directory_path(parcours_doctoral: 'ParcoursDoctoral', filename: str):
    """Return the file upload directory path."""
    return 'parcours_doctoral/{}/{}/{}'.format(
        parcours_doctoral.student.uuid,
        parcours_doctoral.uuid,
        filename,
    )


class ParcoursDoctoralQuerySet(models.QuerySet):
    def annotate_campus_info(self, training_field='training_id', annotation_name='teaching_campus_info'):
        """
        Annotate the queryset with the teaching campus information.
        @param training_field: the name of the training field in the model
        @param annotation_name: the name of the output annotation
        """
        return self.annotate(
            **{
                annotation_name: Subquery(
                    EducationGroupVersion.standard.filter(offer_id=OuterRef(training_field), transition_name='')
                    .select_related('root_group__main_teaching_campus__country')
                    .annotate(
                        main_teaching_campus=JSONObject(
                            uuid=F('root_group__main_teaching_campus__uuid'),
                            name=F('root_group__main_teaching_campus__name'),
                            postal_code=F('root_group__main_teaching_campus__postal_code'),
                            city=F('root_group__main_teaching_campus__city'),
                            country_code=Coalesce(F('root_group__main_teaching_campus__country__iso_code'), Value('')),
                            fr_country_name=Coalesce(F('root_group__main_teaching_campus__country__name'), Value('')),
                            en_country_name=Coalesce(
                                F('root_group__main_teaching_campus__country__name_en'), Value('')
                            ),
                            street=F('root_group__main_teaching_campus__street'),
                            street_number=F('root_group__main_teaching_campus__street_number'),
                            postal_box=F('root_group__main_teaching_campus__postal_box'),
                            location=F('root_group__main_teaching_campus__location'),
                            sic_enrollment_email=F('root_group__main_teaching_campus__sic_enrollment_email'),
                        )
                    )
                    .values('main_teaching_campus')[:1]
                )
            }
        )

    def annotate_training_management_entity(self):
        return self.annotate(
            sigle_entite_gestion=models.Subquery(
                EntityVersion.objects.filter(entity_id=OuterRef("training__management_entity_id"))
                .order_by('-start_date')
                .values("acronym")[:1]
            )
        )

    def annotate_last_status_update(self):
        return self.annotate(
            status_updated_at=Subquery(
                HistoryEntry.objects.filter(
                    object_uuid=OuterRef('uuid'),
                    tags__contains=['parcours_doctoral', 'status-changed'],
                ).values('created')[:1]
            ),
        )

    def annotate_with_student_registration_id(self):
        return self.annotate(
            student_registration_id=models.Subquery(
                Student.objects.filter(person_id=OuterRef('student_id')).values('registration_id')[:1]
            )
        )

    def annotate_with_reference(self):
        """
        Annotate the admission with its reference.
        """
        return self.annotate(
            formatted_reference=Concat(
                # Letter of the campus
                Case(
                    *(
                        When(Q(training__enrollment_campus__name__icontains=name), then=Value(letter))
                        for name, letter in CAMPUS_LETTRE_DOSSIER.items()
                    )
                ),
                Value('-'),
                F('sigle_entite_gestion'),
                # Academic year
                Mod('training__academic_year__year', 100),
                Value('-'),
                # Formatted numero (e.g. 12 -> 0000.0012)
                Replace(ToChar(F('reference'), Value('fm9999,0000,0000')), Value(','), Value('.')),
                output_field=CharField(),
            )
        )


class ParcoursDoctoral(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )
    admission = models.ForeignKey(
        to="admission.DoctorateAdmission",
        verbose_name=pgettext_lazy("parcours_doctoral", "Admission"),
        related_name="+",
        on_delete=models.PROTECT,
    )
    reference = models.BigIntegerField(
        verbose_name=_("Reference"),
        unique=True,
        editable=False,
    )

    created_at = models.DateTimeField(verbose_name=_('Created'), auto_now_add=True)
    modified_at = models.DateTimeField(verbose_name=_('Modified'), auto_now=True)

    student = models.ForeignKey(
        to="base.Person",
        verbose_name=_("Student"),
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

    proximity_commission = models.CharField(
        max_length=255,
        verbose_name=_("Proximity commission"),
        choices=ChoixCommissionProximiteCDEouCLSM.choices()
        + ChoixCommissionProximiteCDSS.choices()
        + ChoixSousDomaineSciences.choices(),
        default='',
        blank=True,
    )

    status = models.CharField(
        choices=ChoixStatutParcoursDoctoral.choices(),
        max_length=64,
        verbose_name=_("Status"),
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

    # Financement
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
    financing_work_contract = models.CharField(
        max_length=255,
        verbose_name=_("Working contract type"),
        default='',
        blank=True,
    )
    financing_eft = models.PositiveSmallIntegerField(
        verbose_name=_("EFT"),
        blank=True,
        null=True,
    )
    scholarship_start_date = models.DateField(
        verbose_name=_("Scholarship start date"),
        null=True,
        blank=True,
    )
    scholarship_end_date = models.DateField(
        verbose_name=_("Scholarship end date"),
        null=True,
        blank=True,
    )
    scholarship_proof = FileField(
        verbose_name=_("Proof of scholarship"),
        upload_to=parcours_doctoral_directory_path,
    )
    planned_duration = models.PositiveSmallIntegerField(
        verbose_name=_("Planned duration"),
        blank=True,
        null=True,
    )
    dedicated_time = models.PositiveSmallIntegerField(
        verbose_name=_("Dedicated time (in EFT)"),
        blank=True,
        null=True,
    )
    is_fnrs_fria_fresh_csc_linked = models.BooleanField(
        verbose_name=_("Is your admission request linked with a FNRS, FRIA, FRESH or CSC application?"),
        null=True,
        blank=True,
    )
    financing_comment = models.TextField(
        verbose_name=_("Financing comment"),
        default='',
        blank=True,
    )

    # Supervision
    supervision_group = SignatureProcessField()

    objects = models.Manager.from_queryset(ParcoursDoctoralQuerySet)()

    class Meta:
        verbose_name = _("Doctoral training")
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
            ('view_confirmation', _("Can view the information related to the confirmation paper")),
            (
                'change_admission_confirmation',
                _("Can update the information related to the confirmation paper"),
            ),
        ]

    @property
    def is_initialized(self):
        return self.status not in STATUTS_DOCTORAT_EN_COURS_DE_CREATION

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        cache.delete('parcours_doctoral_permission_{}'.format(self.uuid))

    @property
    def reference_str(self):
        reference = '{:08}'.format(self.reference)
        return f'{reference[:4]}.{reference[4:]}'

    def __str__(self):
        return self.reference_str


@receiver(post_save, sender=EducationGroupYear)
def _invalidate_doctorate_cache(sender, instance, **kwargs):
    if (
        instance.education_group_type.category == Categories.TRAINING.name
        and instance.education_group_type.name == TrainingType.FORMATION_PHD.name
    ):  # pragma: no branch
        keys = [
            f'parcours_doctoral_permission_{a_uuid}'
            for a_uuid in ParcoursDoctoral.objects.filter(training_id=instance.pk).values_list('uuid', flat=True)
        ]
        if keys:
            cache.delete_many(keys)


@receiver(post_save, sender=Person)
def _invalidate_candidate_cache(sender, instance, **kwargs):
    keys = [
        f'parcours_doctoral_permission_{a_uuid}'
        for a_uuid in ParcoursDoctoral.objects.filter(student_id=instance.pk).values_list('uuid', flat=True)
    ]
    if keys:
        cache.delete_many(keys)
