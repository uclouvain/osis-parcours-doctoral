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
import datetime

from django.contrib import messages
from django.db.models import QuerySet
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy
from django.views import View
from django.views.generic import FormView, TemplateView

from base.models.academic_calendar import AcademicCalendar
from base.models.academic_year import current_academic_year
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.formation.commands import (
    DesinscrireEvaluationCommand,
    InscrireEvaluationCommand,
    ModifierInscriptionEvaluationCommand,
    RecupererInscriptionEvaluationQuery,
)
from parcours_doctoral.ddd.formation.domain.model.enums import StatutActivite
from parcours_doctoral.ddd.formation.dtos.evaluation import InscriptionEvaluationDTO
from parcours_doctoral.forms.training.assessment_enrollment import (
    AssessmentEnrollmentForm,
)
from parcours_doctoral.models import Activity
from parcours_doctoral.utils.assessment_enrollment import (
    assessment_enrollment_is_editable,
)
from parcours_doctoral.views.mixins import (
    ParcoursDoctoralFormMixin,
    ParcoursDoctoralViewMixin,
)

__all__ = [
    'AssessmentEnrollmentCreateView',
    'AssessmentEnrollmentDeleteView',
    'AssessmentEnrollmentDetailsView',
    'AssessmentEnrollmentUpdateView',
]


class BaseAssessmentEnrollmentViewMixin:
    extra_context = {'active_tab': 'assessment-enrollment'}

    @cached_property
    def enrollment_uuid(self):
        return self.kwargs.get('enrollment_uuid', '')

    @cached_property
    def assessment_enrollment(self) -> InscriptionEvaluationDTO:
        return message_bus_instance.invoke(RecupererInscriptionEvaluationQuery(inscription_uuid=self.enrollment_uuid))

    @cached_property
    def current_year(self) -> int:
        if self.enrollment_uuid:
            return self.assessment_enrollment.annee_unite_enseignement

        return self.academic_current_year

    @cached_property
    def academic_current_year(self) -> int:
        return current_academic_year().year

    def assessment_enrollment_is_editable(self):
        return assessment_enrollment_is_editable(
            assessment_enrollment=self.assessment_enrollment,
            academic_year=self.academic_current_year,
        )

    @cached_property
    def related_courses(self) -> QuerySet[Activity]:
        return (
            Activity.objects.filter(status=StatutActivite.ACCEPTEE.name)
            .filter(learning_unit_year__academic_year__year=self.current_year)
            .for_enrollment_courses(self.parcours_doctoral_uuid)
            .order_by('learning_unit_year__acronym')
        )

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        if self.enrollment_uuid:
            context_data['assessment_enrollment'] = self.assessment_enrollment
            context_data['assessment_enrollment_is_editable'] = self.assessment_enrollment_is_editable()

        score_exam_submission_sessions = (
            AcademicCalendar.objects.filter(reference=AcademicCalendarTypes.SCORES_EXAM_SUBMISSION.name)
            .filter(data_year__year=self.current_year)
            .select_related('data_year')
            .order_by('start_date')
        )

        context_data['score_exam_submission_sessions'] = score_exam_submission_sessions
        context_data['today'] = datetime.date.today()
        context_data['current_year'] = self.current_year

        return context_data

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['courses'] = self.related_courses
        return form_kwargs

    def get_success_url(self):
        return resolve_url('parcours_doctoral:assessment-enrollment', uuid=self.parcours_doctoral_uuid)


class AssessmentEnrollmentDetailsView(BaseAssessmentEnrollmentViewMixin, ParcoursDoctoralViewMixin, TemplateView):
    urlpatterns = {'details': '<uuid:enrollment_uuid>'}
    template_name = 'parcours_doctoral/details/training/assessment_enrollment.html'
    permission_required = 'parcours_doctoral.view_assessment_enrollment'


class AssessmentEnrollmentCreateView(BaseAssessmentEnrollmentViewMixin, ParcoursDoctoralFormMixin, FormView):
    urlpatterns = 'add'
    form_class = AssessmentEnrollmentForm
    template_name = 'parcours_doctoral/forms/training/assessment_enrollment.html'
    permission_required = 'parcours_doctoral.change_assessment_enrollment'

    def form_valid(self, form):
        message_bus_instance.invoke(
            InscrireEvaluationCommand(
                cours_uuid=form.cleaned_data['course'],
                session=form.cleaned_data['session'],
                inscription_tardive=form.cleaned_data['late_enrollment'],
            )
        )
        return super().form_valid(form)


class AssessmentEnrollmentUpdateView(BaseAssessmentEnrollmentViewMixin, ParcoursDoctoralFormMixin, FormView):
    urlpatterns = {'update': '<uuid:enrollment_uuid>/update'}
    form_class = AssessmentEnrollmentForm
    template_name = 'parcours_doctoral/forms/training/assessment_enrollment.html'
    permission_required = 'parcours_doctoral.change_assessment_enrollment'

    def has_permission(self):
        return super().has_permission() and self.assessment_enrollment_is_editable()

    def get_initial(self):
        assessment_enrollment = self.assessment_enrollment
        return {
            'course': assessment_enrollment.uuid_activite,
            'session': assessment_enrollment.session,
            'late_enrollment': assessment_enrollment.inscription_tardive,
        }

    def form_valid(self, form):
        message_bus_instance.invoke(
            ModifierInscriptionEvaluationCommand(
                inscription_uuid=self.kwargs['enrollment_uuid'],
                session=form.cleaned_data['session'],
                inscription_tardive=form.cleaned_data['late_enrollment'],
            )
        )
        return super().form_valid(form)


class AssessmentEnrollmentDeleteView(BaseAssessmentEnrollmentViewMixin, ParcoursDoctoralFormMixin, View):
    urlpatterns = {'delete': '<uuid:enrollment_uuid>/delete'}
    permission_required = 'parcours_doctoral.change_assessment_enrollment'
    message_on_success = gettext_lazy('The student has been withdrawn from this assessment.')

    def has_permission(self):
        return super().has_permission() and self.assessment_enrollment_is_editable()

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        message_bus_instance.invoke(
            DesinscrireEvaluationCommand(inscription_uuid=self.kwargs['enrollment_uuid']),
        )
        messages.success(request, self.message_on_success)
        return HttpResponseRedirect(resolve_url('parcours_doctoral:assessment-enrollment', uuid=self.kwargs['uuid']))
