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
from django.core.exceptions import PermissionDenied
from django.shortcuts import resolve_url
from django.views import generic
from django.views.generic import TemplateView
from django.views.generic.edit import FormMixin

from base.models.academic_year import current_academic_year
from parcours_doctoral.ddd.formation.commands import (
    AccepterActivitesCommand,
    RecupererInscriptionsEvaluationsQuery,
    SoumettreActivitesCommand,
)
from parcours_doctoral.ddd.formation.domain.model.enums import StatutActivite
from parcours_doctoral.forms.training.activity import get_category_labels
from parcours_doctoral.forms.training.processus import BatchActivityForm
from parcours_doctoral.models.activity import Activity

__all__ = [
    "AssessmentEnrollmentListView",
    "ComplementaryTrainingView",
    "CourseEnrollmentView",
    "DoctoralTrainingActivityView",
    "TrainingRedirectView",
]

__namespace__ = False

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.utils.assessment_enrollment import (
    assessment_enrollment_is_editable,
)
from parcours_doctoral.views.mixins import ParcoursDoctoralViewMixin


class TrainingRedirectView(ParcoursDoctoralViewMixin, generic.RedirectView):
    """Redirect depending on the status of CDD and parcours_doctoral type"""

    urlpatterns = {'training': 'training'}

    def has_permission(self):
        return True

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.has_perm('parcours_doctoral.view_doctoral_training', self.get_permission_object()):
            return resolve_url('parcours_doctoral:doctoral-training', uuid=self.parcours_doctoral_uuid)
        if self.request.user.has_perm('parcours_doctoral.view_complementary_training', self.get_permission_object()):
            return resolve_url('parcours_doctoral:complementary-training', uuid=self.parcours_doctoral_uuid)
        if self.request.user.has_perm('parcours_doctoral.view_course_enrollment', self.get_permission_object()):
            return resolve_url('parcours_doctoral:course-enrollment', uuid=self.parcours_doctoral_uuid)
        raise PermissionDenied


class TrainingListMixin(ParcoursDoctoralViewMixin, FormMixin):
    form_class = BatchActivityForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activities'] = self.get_queryset()
        context['categories'] = get_category_labels(self.parcours_doctoral.training.management_entity_id)
        context['statuses'] = StatutActivite.choices
        return context

    def get_success_url(self):
        return self.request.get_full_path()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['parcours_doctoral_id'] = self.get_permission_object().pk
        return kwargs

    def form_valid(self, form):
        activity_ids = [activite.uuid for activite in form.cleaned_data['activity_ids']]
        if '_accept' in self.request.POST:
            cmd = AccepterActivitesCommand(
                parcours_doctoral_uuid=self.parcours_doctoral_uuid,
                activite_uuids=activity_ids,
            )
        else:
            cmd = SoumettreActivitesCommand(
                parcours_doctoral_uuid=self.parcours_doctoral_uuid,
                activite_uuids=activity_ids,
            )
        try:
            form.activities_in_error = []
            message_bus_instance.invoke(cmd)
        except MultipleBusinessExceptions as multiple_exceptions:
            for exception in multiple_exceptions.exceptions:
                form.add_error(None, exception.message)
                form.activities_in_error.append(exception.activite_id.uuid)
            return super().form_invalid(form)
        return super().form_valid(form)


class DoctoralTrainingActivityView(TrainingListMixin, generic.FormView):  # pylint: disable=too-many-ancestors
    """List view for doctoral training activities"""

    urlpatterns = {'doctoral-training': 'doctoral-training'}
    template_name = "parcours_doctoral/details/training/training_list.html"
    permission_required = "parcours_doctoral.view_doctoral_training"

    def get_queryset(self):
        return Activity.objects.for_doctoral_training(self.parcours_doctoral_uuid)


class ComplementaryTrainingView(TrainingListMixin, generic.FormView):  # pylint: disable=too-many-ancestors
    urlpatterns = {'complementary-training': 'complementary-training'}
    template_name = "parcours_doctoral/details/training/complementary_training_list.html"
    permission_required = 'parcours_doctoral.view_complementary_training'

    def get_queryset(self):
        return Activity.objects.for_complementary_training(self.parcours_doctoral_uuid)


class CourseEnrollmentView(TrainingListMixin, generic.FormView):  # pylint: disable=too-many-ancestors
    urlpatterns = {'course-enrollment': 'course-enrollment'}
    template_name = "parcours_doctoral/details/training/course_enrollment.html"
    permission_required = 'parcours_doctoral.view_course_enrollment'

    def get_queryset(self):
        return Activity.objects.for_enrollment_courses(self.parcours_doctoral_uuid)


class AssessmentEnrollmentListView(ParcoursDoctoralViewMixin, TemplateView):
    urlpatterns = 'assessment-enrollment'
    template_name = 'parcours_doctoral/details/training/assessment_enrollment_list.html'
    permission_required = 'parcours_doctoral.view_assessment_enrollment'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        assessment_enrollments = message_bus_instance.invoke(
            RecupererInscriptionsEvaluationsQuery(
                parcours_doctoral_uuid=self.parcours_doctoral_uuid,
            )
        )

        editable_assessment_enrollments = set()

        assessment_enrollments_by_session_and_year = {}

        current_year = current_academic_year().year

        for assessment_enrollment in assessment_enrollments:
            if assessment_enrollment_is_editable(
                assessment_enrollment=assessment_enrollment,
                academic_year=current_year,
            ):
                editable_assessment_enrollments.add(assessment_enrollment.uuid)

            year = assessment_enrollment.annee_unite_enseignement
            session = assessment_enrollment.session

            assessment_enrollments_by_session_and_year.setdefault(year, {})

            assessment_enrollments_by_session_and_year[year].setdefault(session, [])
            assessment_enrollments_by_session_and_year[year][session].append(assessment_enrollment)

        context_data['assessment_enrollments'] = assessment_enrollments_by_session_and_year
        context_data['editable_assessment_enrollments'] = editable_assessment_enrollments

        return context_data
