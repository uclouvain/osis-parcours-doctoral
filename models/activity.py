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
import contextlib
from uuid import uuid4

from django.core import validators
from django.db import models
from django.db.models import Prefetch, Q, Sum, When
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from osis_document.contrib import FileField

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from deliberation.models.enums.numero_session import Session
from parcours_doctoral.ddd.formation.domain.model.enums import (
    CategorieActivite,
    ChoixComiteSelection,
    ChoixRolePublication,
    ChoixStatutPublication,
    ChoixTypeVolume,
    ContexteFormation,
    StatutActivite,
    StatutInscriptionEvaluation,
)
from parcours_doctoral.utils.formatting import format_activity_ects

__all__ = [
    "Activity",
    "AssessmentEnrollment",
]


def training_activity_directory_path(instance: 'Activity', filename: str):
    """Return the file upload directory path."""
    return 'parcours_doctoral/{}/{}/training/{}'.format(
        instance.parcours_doctoral.student.uuid,
        instance.parcours_doctoral.uuid,
        filename,
    )


class ActivityQuerySet(models.QuerySet):
    def prefetch_with_assessment_enrollments(self):
        return self.prefetch_related(
            models.Prefetch(
                'assessmentenrollment_set',
                AssessmentEnrollment.objects.with_session_numero().order_by('-session_numero'),
                to_attr='ordered_assessment_enrollments',
            )
        )

    def for_doctoral_training_filter(self):
        return self.filter(
            context=ContexteFormation.DOCTORAL_TRAINING.name,
        ).exclude(Q(category=CategorieActivite.UCL_COURSE.name, course_completed=False))

    def for_doctoral_training(self, parcours_doctoral_uuid):
        return (
            self.for_doctoral_training_filter()
            .filter(parcours_doctoral__uuid=parcours_doctoral_uuid)
            .prefetch_related('children')
            .prefetch_with_assessment_enrollments()
            .select_related(
                'country',
                'parent',
                'learning_unit_year__learning_container_year',
                'learning_unit_year__academic_year',
            )
        )

    def get_doctoral_training_credits_number(self, parcours_doctoral_uuid) -> int:
        """
        Get the total number of credits of the accepted doctoral trainings
        :param parcours_doctoral_uuid: The related doctorate uuid
        :return: The total number of credits
        """
        return (
            self.for_doctoral_training_filter()
            .filter(
                parcours_doctoral__uuid=parcours_doctoral_uuid,
                status=StatutActivite.ACCEPTEE.name,
            )
            .aggregate(ects_total_sum=Sum('ects', default=0))['ects_total_sum']
        )

    def for_complementary_training_filter(self):
        return self.filter(
            context=ContexteFormation.COMPLEMENTARY_TRAINING.name,
        ).exclude(Q(category=CategorieActivite.UCL_COURSE.name, course_completed=False))

    def for_complementary_training(self, parcours_doctoral_uuid):
        return (
            self.for_complementary_training_filter()
            .filter(parcours_doctoral__uuid=parcours_doctoral_uuid)
            .prefetch_with_assessment_enrollments()
            .select_related(
                'country',
                'parent',
                'learning_unit_year__learning_container_year',
                'learning_unit_year__academic_year',
            )
        )

    def has_complementary_training(self, parcours_doctoral_uuid) -> bool:
        """
        Check if the doctorate has at least one accepted complementary training
        :param parcours_doctoral_uuid: The related doctorate uuid
        :return: True if the doctorate has at least one accepted complementary training else False
        """
        return (
            self.for_complementary_training_filter()
            .filter(
                parcours_doctoral__uuid=parcours_doctoral_uuid,
                status=StatutActivite.ACCEPTEE.name,
            )
            .exists()
        )

    def for_enrollment_courses(self, parcours_doctoral_uuid):
        return (
            self.filter(
                parcours_doctoral__uuid=parcours_doctoral_uuid,
                category=CategorieActivite.UCL_COURSE.name,
            )
            .select_related(
                'country',
                'parent',
                'learning_unit_year__learning_container_year',
                'learning_unit_year__academic_year',
            )
            .order_by('context')
        )


class Activity(models.Model):
    uuid = models.UUIDField(
        default=uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )
    parcours_doctoral = models.ForeignKey(
        'parcours_doctoral.ParcoursDoctoral',
        verbose_name=_("Doctorate"),
        on_delete=models.CASCADE,
    )
    context = models.CharField(
        verbose_name=_("Context"),
        max_length=30,
        choices=ContexteFormation.choices(),
        default=ContexteFormation.DOCTORAL_TRAINING.name,
    )
    ects = models.DecimalField(
        verbose_name=_("ECTS credits"),
        help_text=_(
            'Consult the credits grid released by your domain doctoral commission.'
            ' Refer to the website of your commission for more details.'
        ),
        max_digits=3,
        decimal_places=1,
        blank=True,
        default=0,
        validators=[validators.MinValueValidator(0)],
    )
    status = models.CharField(
        max_length=20,
        choices=StatutActivite.choices(),
        default=StatutActivite.NON_SOUMISE.name,
    )
    category = models.CharField(
        max_length=50,
        choices=CategorieActivite.choices(),
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name="children",
        null=True,
        blank=True,
    )

    # Common
    type = models.CharField(
        max_length=100,
        default="",
        blank=True,
        verbose_name=_("Activity type"),
    )

    # Conference, communication, publication
    title = models.CharField(
        max_length=200,
        verbose_name=pgettext_lazy("admission", "Title"),
        default="",
        blank=True,
    )

    participating_proof = FileField(
        verbose_name=_("Participation certification"),
        max_files=2,
        blank=True,
        upload_to=training_activity_directory_path,
    )
    comment = models.TextField(
        verbose_name=_("Comment"),
        default="",
        blank=True,
    )

    # Conference
    start_date = models.DateField(
        verbose_name=_("Activity begin date"),
        null=True,
        blank=True,
    )
    end_date = models.DateField(
        verbose_name=_("Activity end date"),
        null=True,
        blank=True,
    )
    participating_days = models.DecimalField(
        verbose_name=_("Number of days participating"),
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
    )
    is_online = models.BooleanField(
        verbose_name=_("Online event"),
        choices=((False, _("In person")), (True, _("Online"))),
        null=True,
        default=None,  # to prevent messing with choices
        blank=True,
    )
    country = models.ForeignKey(
        'reference.Country',
        verbose_name=_("Country"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    city = models.CharField(
        max_length=100,
        verbose_name=_("City"),
        default="",
        blank=True,
    )
    organizing_institution = models.CharField(
        max_length=100,
        verbose_name=_("Organising institution"),
        default="",
        blank=True,
    )
    website = models.URLField(
        default="",
        verbose_name=pgettext_lazy("admission", "Website"),
        blank=True,
    )

    # communication, publication
    committee = models.CharField(
        max_length=100,
        choices=ChoixComiteSelection.choices(),
        blank=True,
        default="",
    )
    dial_reference = models.CharField(
        max_length=100,
        verbose_name=_("Reference DIAL.Pr"),
        default="",
        blank=True,
    )
    acceptation_proof = FileField(
        verbose_name=_("Participation certification"),
        max_files=1,
        blank=True,
        upload_to=training_activity_directory_path,
    )

    # Communication
    summary = FileField(
        verbose_name=pgettext_lazy("paper summary", "Summary"),
        max_files=1,
        blank=True,
        upload_to=training_activity_directory_path,
    )
    subtype = models.CharField(
        verbose_name=_("Activity subtype"),
        max_length=100,
        default="",
        blank=True,
    )
    subtitle = models.TextField(
        blank=True,
        default="",
    )

    # Publication
    authors = models.CharField(
        verbose_name=_("Authors"),
        max_length=100,
        default="",
        blank=True,
    )
    role = models.CharField(
        verbose_name=pgettext_lazy("activity", "Role"),
        max_length=100,
        choices=ChoixRolePublication.choices(),
        default="",
        blank=True,
    )
    keywords = models.CharField(
        verbose_name=pgettext_lazy("parcours_doctoral", "Keywords"),
        max_length=100,
        default="",
        blank=True,
    )
    journal = models.CharField(
        verbose_name=_("Journal, publishing house or depository institution"),
        max_length=100,
        default="",
        blank=True,
    )
    is_publication_national = models.BooleanField(
        verbose_name=_("Is publication national"),
        choices=((False, _("International publication")), (True, _("National publication"))),
        default=None,
        null=True,
        blank=True,
    )
    with_reading_committee = models.BooleanField(
        verbose_name=_("With reading committee"),
        choices=((False, _("Without reading committee")), (True, _("With reading committee"))),
        default=None,
        null=True,
        blank=True,
    )

    publication_status = models.CharField(
        max_length=100,
        choices=ChoixStatutPublication.choices(),
        blank=True,
        default="",
    )

    # Seminaires
    hour_volume = models.CharField(
        verbose_name=_("Total hourly volume"),
        max_length=100,
        default="",
        blank=True,
    )
    hour_volume_type = models.CharField(
        verbose_name=_("Hourly volume type"),
        max_length=100,
        default="",
        choices=ChoixTypeVolume.choices(),
        blank=True,
    )

    # UCL Course
    learning_unit_year = models.ForeignKey(
        'base.LearningUnitYear',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    course_completed = models.BooleanField(
        blank=True,
        default=False,
    )
    mark = models.CharField(
        verbose_name=_("Mark or honours obtained"),
        max_length=100,
        default="",
        blank=True,
    )

    # Process
    reference_promoter_assent = models.BooleanField(
        verbose_name=_("Lead supervisor assent"),
        null=True,
    )
    reference_promoter_comment = models.TextField(
        verbose_name=_("Lead supervisor comment"),
        default="",
    )
    cdd_comment = models.TextField(
        verbose_name=_("CDD manager comment"),
        default="",
    )

    # Management
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=pgettext_lazy("admission", "Created at"),
    )
    modified_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Modified at"),
    )
    can_be_submitted = models.BooleanField(
        default=False,
        verbose_name=_("Can be submitted"),
    )

    objects = models.Manager.from_queryset(ActivityQuerySet)()

    def __repr__(self):
        return f"{self.get_category_display()} ({self.ects} ects, {self.get_status_display()})"

    def __str__(self) -> str:
        return f"{self.get_category_display()} - {format_activity_ects(self.ects)}"

    class Meta:
        verbose_name = _("Training activity")
        verbose_name_plural = _("Training activities")
        ordering = ['-created_at']


@receiver(post_save, sender=Activity)
def _activity_update_can_be_submitted(sender, instance, **kwargs):
    from parcours_doctoral.ddd.formation.builder.activite_identity_builder import (
        ActiviteIdentityBuilder,
    )
    from parcours_doctoral.ddd.formation.domain.service.soumettre_activites import (
        SoumettreActivites,
    )
    from parcours_doctoral.infrastructure.parcours_doctoral.formation.repository.activite import (
        ActiviteRepository,
    )

    activite_identity = ActiviteIdentityBuilder.build_from_uuid(instance.uuid)
    activite = ActiviteRepository.get(activite_identity)
    activite_dto = ActiviteRepository.get_dto(activite_identity)
    can_be_submitted = False

    # When communication seminar activity, update the parent uuid
    is_communication_seminar = (
        activite.categorie == CategorieActivite.COMMUNICATION
        and activite.categorie_parente == CategorieActivite.SEMINAR
    )
    instance_uuid = instance.uuid if not is_communication_seminar else instance.parent.uuid

    with contextlib.suppress(MultipleBusinessExceptions):
        SoumettreActivites().verifier_activite(activite, activite_dto, ActiviteRepository())

        if is_communication_seminar:
            # We must also trigger parent check (to check all children) for communication seminar activities
            instance.parent.save()
            return

        can_be_submitted = True
    Activity.objects.filter(uuid=instance_uuid).update(can_be_submitted=can_be_submitted)


@receiver(post_delete, sender=Activity)
def _activity_update_seminar_can_be_submitted(sender, instance, **kwargs):
    # When communication seminar activity is deleted, trigger a parent seminar update
    if (
        instance.category == CategorieActivite.COMMUNICATION.name
        and instance.parent_id == CategorieActivite.SEMINAR.name
    ):
        instance.parent.save()


class AssessmentEnrollmentQuerySet(models.QuerySet):
    SESSION_MAPPING = [
        When(session=session_enum.name, then=Session.get_numero_session(session_enum.name)) for session_enum in Session
    ]

    def with_session_numero(self):
        return self.annotate(session_numero=models.Case(*self.SESSION_MAPPING))


class AssessmentEnrollment(models.Model):
    objects = models.Manager.from_queryset(AssessmentEnrollmentQuerySet)()

    uuid = models.UUIDField(
        db_index=True,
        default=uuid4,
        editable=False,
        unique=True,
    )

    course = models.ForeignKey(
        limit_choices_to=Q(category=CategorieActivite.UCL_COURSE.name),
        on_delete=models.CASCADE,
        to=Activity,
        verbose_name=_("Course"),
    )

    session = models.CharField(
        choices=Session.choices(),
        max_length=255,
        verbose_name=_("Session"),
    )

    status = models.CharField(
        choices=StatutInscriptionEvaluation.choices(),
        max_length=255,
        verbose_name=_("Status"),
    )

    late_enrollment = models.BooleanField(
        verbose_name=_("Late enrollment"),
    )

    late_unenrollment = models.BooleanField(
        verbose_name=_("Late unenrollment"),
        default=False,
    )

    submitted_mark = models.CharField(
        verbose_name=_('Submitted mark'),
        max_length=20,
        default='',
        blank=True,
        null=False,
    )

    corrected_mark = models.CharField(
        verbose_name=_("Corrected mark"),
        max_length=20,
        default="",
        blank=True,
        null=False,
    )
