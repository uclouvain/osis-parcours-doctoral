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
import itertools

from django.conf import settings
from django.contrib import admin
from django.db import models
from django.forms import BooleanField, ModelForm
from django.forms.widgets import HiddenInput
from django.shortcuts import resolve_url
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from django_json_widget.widgets import JSONEditorWidget
from hijack.contrib.admin import HijackUserAdminMixin
from osis_document_components.fields import FileField
from osis_mail_template.admin import MailTemplateAdmin

from base.models.entity_version import EntityVersion
from education_group.contrib.admin import EducationGroupRoleModelAdmin
from osis_role.contrib.admin import RoleModelAdmin
from parcours_doctoral.auth.roles.adre_manager import AdreManager
from parcours_doctoral.auth.roles.adre_secretary import AdreSecretary
from parcours_doctoral.auth.roles.auditor import Auditor
from parcours_doctoral.auth.roles.cdd_configurator import CddConfigurator
from parcours_doctoral.auth.roles.das import SectorAdministrativeDirector
from parcours_doctoral.auth.roles.doctorate_reader import DoctorateReader
from parcours_doctoral.auth.roles.jury_member import JuryMember
from parcours_doctoral.auth.roles.jury_secretary import JurySecretary
from parcours_doctoral.auth.roles.sceb_manager import ScebManager
from parcours_doctoral.auth.roles.student import Student
from parcours_doctoral.ddd.formation.domain.model.enums import (
    CategorieActivite,
    ContexteFormation,
    StatutInscriptionEvaluation,
)
from parcours_doctoral.models import (
    AssessmentEnrollment,
    ConfirmationPaper,
    ParcoursDoctoral,
)
from parcours_doctoral.models.activity import Activity
from parcours_doctoral.models.cdd_config import CddConfiguration
from parcours_doctoral.models.cdd_mail_template import CddMailTemplate
from parcours_doctoral.models.private_defense import PrivateDefense
from parcours_doctoral.models.thesis_distribution_authorization import (
    ThesisDistributionAuthorizationActor,
)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'context', 'get_category', 'ects', 'modified_at', 'status', 'is_course_completed')
    search_fields = [
        'parcours_doctoral__uuid',
    ]
    list_filter = [
        'context',
        'category',
        'status',
    ]
    fields = [
        'parcours_doctoral',
        'category',
        'parent',
        'ects',
        'course_completed',
        "type",
        "title",
        "participating_proof",
        "comment",
        "start_date",
        "end_date",
        "participating_days",
        "is_online",
        "country",
        "city",
        "organizing_institution",
        "website",
        "committee",
        "dial_reference",
        "acceptation_proof",
        "summary",
        "subtype",
        "subtitle",
        "authors",
        "role",
        "keywords",
        "journal",
        "publication_status",
        "hour_volume",
        "learning_unit_year",
        "learning_class_year",
        "can_be_submitted",
    ]
    readonly_fields = [
        'parcours_doctoral',
        'category',
        'parent',
        "type",
        "title",
        "participating_proof",
        "comment",
        "start_date",
        "end_date",
        "participating_days",
        "is_online",
        "country",
        "city",
        "organizing_institution",
        "website",
        "committee",
        "dial_reference",
        "acceptation_proof",
        "summary",
        "subtype",
        "subtitle",
        "authors",
        "role",
        "keywords",
        "journal",
        "publication_status",
        "hour_volume",
        "learning_unit_year",
        "learning_class_year",
        "can_be_submitted",
    ]
    list_select_related = ['parcours_doctoral', 'parent']

    @admin.display(description=_('Course completed'), boolean=True)
    def is_course_completed(self, obj: Activity):
        if obj.category == CategorieActivite.UCL_COURSE.name:
            return obj.course_completed

    @admin.display(description=_('Category'))
    def get_category(self, obj: Activity):
        if obj.parent_id:
            return f"({obj.parent.category}) {obj.category}"
        return obj.category

    @staticmethod
    def view_on_site(obj):
        context_mapping = {
            ContexteFormation.DOCTORAL_TRAINING.name: 'doctoral-training',
            ContexteFormation.COMPLEMENTARY_TRAINING.name: 'complementary-training',
        }
        context = (
            context_mapping[obj.context] if obj.category != CategorieActivite.UCL_COURSE.name else 'course-enrollment'
        )
        url = resolve_url(f'parcours_doctoral:{context}', uuid=obj.parcours_doctoral.uuid)
        return url + f'#{obj.uuid}'


@admin.register(AssessmentEnrollment)
class AssessmentEnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        'uuid',
        'related_doctorate',
        'course_year',
        'session',
        'course_acronym',
        'active',
        'submitted_mark',
        'corrected_mark',
    )
    autocomplete_fields = [
        'course',
    ]

    @admin.display(description=_('Active'), boolean=True)
    def active(self, obj):
        return obj.status == StatutInscriptionEvaluation.ACCEPTEE.name

    @admin.display(description=_('Academic year'))
    def course_year(self, obj):
        return obj.learning_year_academic_year

    @admin.display(description=_('Related doctorate'))
    def related_doctorate(self, obj):
        return obj.course.parcours_doctoral.reference

    @admin.display(description=_('Learning unit'))
    def course_acronym(self, obj):
        return obj.learning_year_acronym

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate_with_learning_year_info()
            .select_related(
                'course__parcours_doctoral',
            )
            .order_by(
                'course__parcours_doctoral__reference',
                'learning_year_academic_year',
                'learning_year_acronym',
            )
        )


@admin.register(CddMailTemplate)
class CddMailTemplateAdmin(MailTemplateAdmin):
    list_display = ('name', 'identifier', 'language', 'cdd')
    search_fields = [
        'cdd__acronym',
        'idenfier',
    ]
    autocomplete_fields = [
        'cdd',
    ]
    list_filter = [
        'cdd',
        'language',
        'identifier',
    ]

    @staticmethod
    def view_on_site(obj):
        return resolve_url(f'parcours_doctoral:config:cdd-mail-template:preview', identifier=obj.identifier, pk=obj.pk)


@admin.register(
    AdreManager,
    AdreSecretary,
    DoctorateReader,
    JuryMember,
    JurySecretary,
    ScebManager,
    SectorAdministrativeDirector,
    Student,
)
class HijackRoleModelAdmin(HijackUserAdminMixin, RoleModelAdmin):
    list_select_related = ['person__user']

    def get_hijack_user(self, obj):
        return obj.person.user


@admin.register(Auditor)
class HijackRoleModelAdmin(HijackUserAdminMixin, RoleModelAdmin):
    list_display = ('person', 'entity', 'with_child')
    list_select_related = ['person__user']

    def get_hijack_user(self, obj):
        return obj.person.user


@admin.register(CddConfigurator)
class CddConfiguratorAdmin(HijackRoleModelAdmin):
    list_display = ('person', 'most_recent_acronym')
    search_fields = [
        'person__first_name',
        'person__last_name',
        'entity__entityversion__acronym',
    ]
    autocomplete_fields = [
        'entity',
    ]

    @admin.display(description=pgettext_lazy('admission', 'Entity'))
    def most_recent_acronym(self, obj):
        return obj.most_recent_acronym

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                most_recent_acronym=models.Subquery(
                    EntityVersion.objects.filter(
                        entity__id=models.OuterRef('entity_id'),
                    )
                    .order_by("-start_date")
                    .values('acronym')[:1]
                )
            )
        )


@admin.register(CddConfiguration)
class CddConfigurationAdmin(admin.ModelAdmin):
    autocomplete_fields = [
        'cdd',
    ]


class ReadOnlyFilesMixin:
    def get_readonly_fields(self, request, obj=None):
        # Also mark all FileField as readonly (since we don't have admin widget yet)
        return [
            field
            for field in itertools.chain(
                self.readonly_fields,
                (
                    field.name
                    for field in self.model._meta.get_fields(include_parents=True)
                    if isinstance(field, FileField)
                ),
            )
        ]


@admin.register(ParcoursDoctoral)
class ParcoursDoctoralAdmin(ReadOnlyFilesMixin, admin.ModelAdmin):
    list_display = [
        'student_fmt',
        'training',
        'status',
        'view_on_portal',
    ]
    autocomplete_fields = [
        'admission',
        'training',
        'thesis_institute',
        'international_scholarship',
        'thesis_language',
        'student',
    ]
    search_fields = [
        'student__global_id',
        'student__last_name',
        'student__first_name',
    ]
    list_select_related = [
        'student',
        'training__academic_year',
    ]
    list_filter = [
        'status',
    ]
    readonly_fields = [
        'uuid',
    ]

    @admin.display(description=pgettext_lazy('parcours_doctoral', 'Student'))
    def student_fmt(self, obj):
        return '{} ({global_id})'.format(obj.student, global_id=obj.student.global_id)

    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

    def has_add_permission(self, request):
        # Prevent adding from admin site as we lose all business checks
        return False

    @admin.display(description=_('Search on portal'))
    def view_on_portal(self, obj):
        url = f"{settings.OSIS_PORTAL_URL}admin/auth/user/?q={obj.student.global_id}"
        return mark_safe(f'<a class="button" href="{url}" target="_blank">{_("Student on portal")}</a>')


@admin.register(ConfirmationPaper)
class ConfirmationPaperAdmin(ReadOnlyFilesMixin, admin.ModelAdmin):
    list_display = [
        'parcours_doctoral_reference',
        'is_active',
        'confirmation_date',
    ]
    search_fields = [
        'parcours_doctoral__reference',
        'parcours_doctoral__student__last_name',
        'parcours_doctoral__student__first_name',
    ]
    autocomplete_fields = [
        'parcours_doctoral',
    ]
    ordering = [
        'parcours_doctoral__reference',
        '-created_at',
    ]
    list_select_related = [
        'parcours_doctoral',
    ]

    @admin.display(description=_('Related doctorate'))
    def parcours_doctoral_reference(self, obj):
        return obj.parcours_doctoral.reference


class PrivateDefenseAdminForm(ModelForm):
    is_active = BooleanField(
        label=_('Is active'),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['is_active'].initial = (
            self.instance.current_parcours_doctoral_id == self.instance.parcours_doctoral_id
        )

    class Meta:
        model = PrivateDefense
        exclude = ['current_parcours_doctoral']

    def save(self, commit=True):
        instance = super().save(commit=False)

        instance.current_parcours_doctoral = instance.parcours_doctoral if self.cleaned_data['is_active'] else None

        if commit:
            instance.save()

        return instance


@admin.register(PrivateDefense)
class PrivateDefenseAdmin(ReadOnlyFilesMixin, admin.ModelAdmin):
    form = PrivateDefenseAdminForm
    list_display = [
        'parcours_doctoral_reference',
        'is_active',
        'datetime',
    ]
    search_fields = [
        'parcours_doctoral__reference',
        'parcours_doctoral__student__last_name',
        'parcours_doctoral__student__first_name',
    ]
    autocomplete_fields = [
        'parcours_doctoral',
    ]
    ordering = [
        'parcours_doctoral__reference',
        '-created_at',
    ]
    list_select_related = [
        'parcours_doctoral',
    ]

    @admin.display(description=_('Related doctorate'))
    def parcours_doctoral_reference(self, obj):
        return obj.parcours_doctoral.reference

    @admin.display(description=_('Is active'))
    def is_active(self, obj):
        return bool(obj.current_parcours_doctoral_id)


@admin.register(ThesisDistributionAuthorizationActor)
class ThesisDistributionAuthorizationActorAdmin(admin.ModelAdmin):
    pass
