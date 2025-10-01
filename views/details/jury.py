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
from django.urls import reverse
from django.views.generic import FormView, TemplateView
from rest_framework.settings import api_settings

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.jury.commands import (
    AjouterMembreCommand,
    VerifierJuryConditionSignatureQuery,
)
from parcours_doctoral.ddd.jury.domain.model.enums import RoleJury
from parcours_doctoral.ddd.jury.domain.validator.exceptions import (
    MembreDejaDansJuryException,
    MembreExterneSansEmailException,
    MembreExterneSansGenreException,
    MembreExterneSansInstitutionException,
    MembreExterneSansNomException,
    MembreExterneSansPaysException,
    MembreExterneSansPrenomException,
    MembreExterneSansTitreException,
    NonDocteurSansJustificationException,
)
from parcours_doctoral.forms.jury.approval import JuryApprovalForm
from parcours_doctoral.forms.jury.membre import ApprovalByPdfForm, JuryMembreForm
from parcours_doctoral.utils.ddd import gather_business_exceptions
from parcours_doctoral.views.mixins import (
    BusinessExceptionFormViewMixin,
    ParcoursDoctoralViewMixin,
)

__all__ = [
    'JuryPreparationDetailView',
    'JuryView',
]
__namespace__ = False


class JuryPreparationDetailView(ParcoursDoctoralViewMixin, TemplateView):
    urlpatterns = 'jury-preparation'
    template_name = 'parcours_doctoral/details/jury/preparation.html'
    permission_required = 'parcours_doctoral.view_jury'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['jury'] = self.jury
        context['cotutelle'] = self.cotutelle
        return context


class JuryView(
    ParcoursDoctoralViewMixin,
    BusinessExceptionFormViewMixin,
    FormView,
):
    urlpatterns = 'jury'
    template_name = 'parcours_doctoral/forms/jury/jury.html'
    permission_required = 'parcours_doctoral.view_jury'
    form_class = JuryMembreForm
    error_mapping = {
        NonDocteurSansJustificationException: "justification_non_docteur",
        MembreExterneSansInstitutionException: "institution",
        MembreExterneSansPaysException: "pays",
        MembreExterneSansNomException: "nom",
        MembreExterneSansPrenomException: "prenom",
        MembreExterneSansTitreException: "titre",
        MembreExterneSansGenreException: "genre",
        MembreExterneSansEmailException: "email",
        MembreDejaDansJuryException: "matricule",
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['jury'] = self.jury

        data = gather_business_exceptions(VerifierJuryConditionSignatureQuery(uuid_jury=self.parcours_doctoral_uuid))
        context['signature_conditions'] = data.get(api_settings.NON_FIELD_ERRORS_KEY, [])

        context['membre_president'] = [membre for membre in self.jury.membres if membre.role == RoleJury.PRESIDENT.name]
        context['membre_secretaire'] = [
            membre for membre in self.jury.membres if membre.role == RoleJury.SECRETAIRE.name
        ]
        context['membre_verificateur'] = [
            membre for membre in self.jury.membres if membre.role == RoleJury.VERIFICATEUR.name
        ]
        context['membre_cdd'] = [membre for membre in self.jury.membres if membre.role == RoleJury.CDD.name]
        context['membre_adre'] = [membre for membre in self.jury.membres if membre.role == RoleJury.ADRE.name]
        context['membres'] = [membre for membre in self.jury.membres if membre.role == RoleJury.MEMBRE.name]
        if not self.request.user.has_perm('parcours_doctoral.change_jury', obj=self.get_permission_object()):
            del context['form']
        if self.request.user.has_perm('parcours_doctoral.jury_reset_signatures', obj=self.get_permission_object()):
            context['approve_by_pdf_form'] = ApprovalByPdfForm()
        if self.request.user.has_perm('parcours_doctoral.approve_jury', obj=self.get_permission_object()):
            if 'jury_approval_data' in self.request.session:
                # Get data and errors from JuryCddDecisionView
                approval_form = JuryApprovalForm(data=self.request.session.pop('jury_approval_data'))
                approval_form._errors = self.request.session.pop('jury_approval_errors')
                context['approval_form'] = approval_form
            else:
                context['approval_form'] = JuryApprovalForm()
        return context

    def call_command(self, form):
        message_bus_instance.invoke(
            AjouterMembreCommand(
                uuid_jury=self.parcours_doctoral_uuid,
                **form.cleaned_data,
            )
        )

    def get_success_url(self):
        return reverse('parcours_doctoral:jury', args=[self.parcours_doctoral_uuid])
