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
from typing import Optional

from django.db.models import Q
from django.forms import Form
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, resolve_url
from django.utils.functional import cached_property
from django.views import generic
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormMixin

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.formation.commands import (
    RefuserActiviteCommand,
    RevenirSurStatutActiviteCommand,
)
from parcours_doctoral.ddd.formation.domain.model.enums import CategorieActivite
from parcours_doctoral.forms.training.activity import *
from parcours_doctoral.forms.training.activity import UclCompletedCourseForm
from parcours_doctoral.forms.training.processus import RefuseForm
from parcours_doctoral.models.activity import Activity
from parcours_doctoral.views.mixins import (
    ParcoursDoctoralFormMixin,
    ParcoursDoctoralViewMixin,
)

__all__ = [
    "TrainingActivityAddView",
    "TrainingActivityDeleteView",
    "TrainingActivityEditView",
    "TrainingActivityRefuseView",
    "TrainingActivityRequireChangesView",
    "TrainingActivityRestoreView",
]
__namespace__ = {
    'doctoral-training': 'doctoral-training',
    'complementary-training': 'complementary-training',
    'course-enrollment': 'course-enrollment',
}


class TrainingActivityFormMixin(ParcoursDoctoralFormMixin, ParcoursDoctoralViewMixin):
    """Form mixin for an activity"""

    template_name = "parcours_doctoral/forms/training.html"
    model = Activity
    form_class_mapping = {
        "doctoral-training": {
            CategorieActivite.CONFERENCE: ConferenceForm,
            (CategorieActivite.CONFERENCE, CategorieActivite.COMMUNICATION): ConferenceCommunicationForm,
            (CategorieActivite.CONFERENCE, CategorieActivite.PUBLICATION): ConferencePublicationForm,
            CategorieActivite.RESIDENCY: ResidencyForm,
            (CategorieActivite.RESIDENCY, CategorieActivite.COMMUNICATION): ResidencyCommunicationForm,
            CategorieActivite.COMMUNICATION: CommunicationForm,
            CategorieActivite.PUBLICATION: PublicationForm,
            CategorieActivite.SERVICE: ServiceForm,
            CategorieActivite.SEMINAR: SeminarForm,
            (CategorieActivite.SEMINAR, CategorieActivite.COMMUNICATION): SeminarCommunicationForm,
            CategorieActivite.VAE: ValorisationForm,
            CategorieActivite.COURSE: CourseForm,
            CategorieActivite.UCL_COURSE: UclCompletedCourseForm,
            CategorieActivite.PAPER: PaperForm,
        },
        "complementary-training": {
            CategorieActivite.COURSE: ComplementaryCourseForm,
            CategorieActivite.UCL_COURSE: UclCompletedCourseForm,
        },
        "course-enrollment": {
            CategorieActivite.UCL_COURSE: UclCourseForm,
        },
    }

    @property
    def namespace(self) -> str:
        return self.request.resolver_match.namespaces[1]

    def get_permission_required(self):
        return ["parcours_doctoral.change_activity", f"parcours_doctoral.view_{self.namespace.replace('-', '_')}"]

    @property
    def category(self) -> str:
        """Return category being worked on"""
        category = self.activity.category if hasattr(self, 'activity') else self.kwargs['category']
        return str(category).upper()

    @cached_property
    def parent(self) -> Optional[Activity]:
        if hasattr(self, 'activity'):
            if self.activity.parent_id:
                return self.activity.parent
        else:
            parent_id = self.request.GET.get('parent')
            if parent_id:
                return get_object_or_404(Activity, uuid=parent_id)

    @property
    def category_mapping_key(self):
        """Return the form_class mapping key (with parent if needed)"""
        category = CategorieActivite[self.category]
        if self.parent:
            return CategorieActivite[str(self.parent.category)], category
        return category

    def get_form_class(self):
        try:
            return self.form_class_mapping[self.namespace][self.category_mapping_key]
        except KeyError as e:
            raise Http404(f"No form mapped: {e}")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['parcours_doctoral'] = self.get_permission_object()
        return kwargs

    def get_success_url(self):
        base_url = resolve_url(':'.join(self.request.resolver_match.namespaces), uuid=self.parcours_doctoral_uuid)
        return f"{base_url}#{self.object.uuid}"


class TrainingActivityAddView(TrainingActivityFormMixin, generic.CreateView):
    urlpatterns = {'add': 'add/<str:category>'}
    object = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        params = {'parcours_doctoral': kwargs['parcours_doctoral'], 'category': self.category}
        if self.parent:
            params['parent'] = self.parent
        self.object = kwargs['instance'] = Activity(**params)
        return kwargs


class TrainingActivityEditView(TrainingActivityFormMixin, generic.UpdateView):
    urlpatterns = {'edit': 'edit/<uuid:activity_id>'}
    slug_field = 'uuid'
    pk_url_kwarg = None
    slug_url_kwarg = 'activity_id'

    @property
    def activity(self):
        # Don't remove, this is to share same template code in front-office
        return self.object


class TrainingActivityDeleteView(ParcoursDoctoralFormMixin, ParcoursDoctoralViewMixin, generic.DeleteView):
    urlpatterns = {'delete': 'delete/<uuid:activity_id>'}
    model = Activity
    slug_field = 'uuid'
    pk_url_kwarg = "NOT_TO_BE_USED"
    slug_url_kwarg = 'activity_id'
    template_name = "parcours_doctoral/forms/training/activity_confirm_delete.html"

    def get_permission_required(self):
        return [
            "parcours_doctoral.delete_activity",
            f"parcours_doctoral.view_{self.request.resolver_match.namespaces[1].replace('-', '_')}",
        ]

    def form_valid(self, form):
        Activity.objects.filter(
            Q(uuid=self.kwargs['activity_id']) | Q(parent__uuid=self.kwargs['activity_id'])
        ).delete()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return resolve_url(':'.join(self.request.resolver_match.namespaces), uuid=self.parcours_doctoral_uuid)


class TrainingActivityActionFormMixin(
    ParcoursDoctoralFormMixin, ParcoursDoctoralViewMixin, SingleObjectMixin, FormMixin
):
    model = Activity
    slug_field = 'uuid'
    pk_url_kwarg = "NOT_TO_BE_USED"
    slug_url_kwarg = 'activity_id'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_permission_required(self):
        return [
            self.permission_required,
            f"parcours_doctoral.view_{self.request.resolver_match.namespaces[1].replace('-', '_')}",
        ]

    @property
    def activity(self) -> Activity:
        # Don't remove, this is to share same template code in front-office
        return self.object

    def get_success_url(self):
        base_url = resolve_url(':'.join(self.request.resolver_match.namespaces), uuid=self.parcours_doctoral_uuid)
        return f"{base_url}#{self.object.uuid}"


class TrainingActivityRefuseView(TrainingActivityActionFormMixin, generic.FormView):
    urlpatterns = {'refuse': 'refuse/<uuid:activity_id>'}
    permission_required = "parcours_doctoral.refuse_activity"
    template_name = "parcours_doctoral/forms/training/activity_refuse.html"
    form_class = RefuseForm
    avec_modification = False

    def form_valid(self, form):
        message_bus_instance.invoke(
            RefuserActiviteCommand(
                parcours_doctoral_uuid=self.parcours_doctoral_uuid,
                activite_uuid=self.kwargs['activity_id'],
                avec_modification=self.avec_modification,
                remarque=form.cleaned_data['reason'],
            )
        )
        return super().form_valid(form)


class TrainingActivityRequireChangesView(TrainingActivityRefuseView):
    urlpatterns = {'require-changes': 'require-changes/<uuid:activity_id>'}
    avec_modification = True
    template_name = "parcours_doctoral/forms/training/activity_require_changes.html"


class TrainingActivityRestoreView(TrainingActivityActionFormMixin, generic.FormView):
    urlpatterns = {'restore': 'restore/<uuid:activity_id>'}
    permission_required = "parcours_doctoral.restore_activity"
    template_name = "parcours_doctoral/forms/training/activity_restore.html"
    form_class = Form

    def form_valid(self, form):
        message_bus_instance.invoke(RevenirSurStatutActiviteCommand(activite_uuid=self.kwargs['activity_id']))
        return super().form_valid(form)
