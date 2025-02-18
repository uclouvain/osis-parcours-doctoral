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
from django.shortcuts import redirect, resolve_url
from django.views import generic
from django.views.generic.edit import FormMixin

from parcours_doctoral.ddd.formation.commands import (
    AccepterActivitesCommand,
    SoumettreActivitesCommand,
)
from parcours_doctoral.ddd.formation.domain.model.enums import StatutActivite
from parcours_doctoral.exports.training_recap import (
    parcours_doctoral_pdf_formation_doctorale,
)
from parcours_doctoral.forms.training.activity import get_category_labels
from parcours_doctoral.forms.training.processus import BatchActivityForm
from parcours_doctoral.models.activity import Activity

__all__ = [
    "ComplementaryTrainingView",
    "CourseEnrollmentView",
    "DoctoralTrainingActivityView",
    "TrainingRedirectView",
    "TrainingRecapPdfView",
]

__namespace__ = False

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from infrastructure.messages_bus import message_bus_instance
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


class TrainingRecapPdfView(ParcoursDoctoralViewMixin, generic.View):
    urlpatterns = {'training_pdf_recap': 'pdf_recap'}
    permission_required = "parcours_doctoral.view_doctoral_training"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activities'] = Activity.objects.for_doctoral_training(self.parcours_doctoral_uuid).filter(
            status=StatutActivite.ACCEPTEE.name
        )
        return context

    def get(self, request, *args, **kwargs):
        file_url = parcours_doctoral_pdf_formation_doctorale(
            parcours_doctoral=self.parcours_doctoral_dto,
            context=self.get_context_data(),
            language=self.parcours_doctoral.student.language,
        )
        return redirect(file_url)
