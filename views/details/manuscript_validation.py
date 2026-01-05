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
from django.shortcuts import resolve_url
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy
from django.views.generic import FormView

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.autorisation_diffusion_these.commands import (
    AccepterTheseParAdreCommand,
    AccepterTheseParScebCommand,
    RecupererAutorisationDiffusionTheseQuery,
    RefuserTheseParAdreCommand,
    RefuserTheseParScebCommand,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.enums import (
    CHOIX_STATUTS_AUTORISATION_DIFFUSION_THESE_MODIFIABLE_PAR_ADRE,
    CHOIX_STATUTS_AUTORISATION_DIFFUSION_THESE_MODIFIABLE_PAR_SCEB,
    ChoixEtatSignature,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.dtos.autorisation_diffusion_these import (
    AutorisationDiffusionTheseDTO,
)
from parcours_doctoral.forms.manuscript_validation import (
    ManuscriptValidationApprovalForm,
)
from parcours_doctoral.views.mixins import (
    BusinessExceptionFormViewMixin,
    ParcoursDoctoralFormMixin,
)

__all__ = [
    'ManuscriptValidationView',
]

__namespace__ = False


class ManuscriptValidationView(
    ParcoursDoctoralFormMixin,
    BusinessExceptionFormViewMixin,
    FormView,
):
    urlpatterns = 'manuscript-validation'
    template_name = 'parcours_doctoral/forms/manuscript_validation.html'
    form_class = ManuscriptValidationApprovalForm
    extra_context = {'submit_label': gettext_lazy('Submit my decision')}
    permission_required_by_http_method = {
        'GET': 'parcours_doctoral.view_manuscript_validation',
        'POST': 'parcours_doctoral.validate_manuscript',
    }

    def get_permission_required(self):
        return (self.permission_required_by_http_method[self.request.method],)

    def get_form(self, form_class=None):
        if self.request.user.has_perm(perm='parcours_doctoral.validate_manuscript', obj=self.parcours_doctoral):
            return super().get_form(form_class=form_class)
        return None

    @cached_property
    def authorization_distribution(self) -> AutorisationDiffusionTheseDTO:
        return message_bus_instance.invoke(
            RecupererAutorisationDiffusionTheseQuery(
                uuid_parcours_doctoral=self.parcours_doctoral_uuid,
            )
        )

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['authorization_distribution'] = self.authorization_distribution
        context_data['signatories'] = {
            signatory.role: signatory for signatory in self.authorization_distribution.signataires
        }
        return context_data

    def call_command(self, form):
        decision = form.cleaned_data.get('decision', None)

        authorization_distribution = self.authorization_distribution

        if authorization_distribution.statut in CHOIX_STATUTS_AUTORISATION_DIFFUSION_THESE_MODIFIABLE_PAR_ADRE:
            if decision == ChoixEtatSignature.DECLINED.name:
                message_bus_instance.invoke(
                    RefuserTheseParAdreCommand(
                        uuid_parcours_doctoral=self.parcours_doctoral_uuid,
                        matricule_adre=self.request.user.person.global_id,
                        motif_refus=form.cleaned_data['motif_refus'],
                        commentaire_interne=form.cleaned_data['commentaire_interne'],
                        commentaire_externe=form.cleaned_data['commentaire_externe'],
                    )
                )
            elif decision == ChoixEtatSignature.APPROVED.name:
                message_bus_instance.invoke(
                    AccepterTheseParAdreCommand(
                        uuid_parcours_doctoral=self.parcours_doctoral_uuid,
                        matricule_adre=self.request.user.person.global_id,
                        commentaire_interne=form.cleaned_data['commentaire_interne'],
                        commentaire_externe=form.cleaned_data['commentaire_externe'],
                    )
                )

        elif authorization_distribution.statut in CHOIX_STATUTS_AUTORISATION_DIFFUSION_THESE_MODIFIABLE_PAR_SCEB:
            if decision == ChoixEtatSignature.DECLINED.name:
                message_bus_instance.invoke(
                    RefuserTheseParScebCommand(
                        uuid_parcours_doctoral=self.parcours_doctoral_uuid,
                        matricule_sceb=self.request.user.person.global_id,
                        motif_refus=form.cleaned_data['motif_refus'],
                        commentaire_interne=form.cleaned_data['commentaire_interne'],
                        commentaire_externe=form.cleaned_data['commentaire_externe'],
                    )
                )
            elif decision == ChoixEtatSignature.APPROVED.name:
                message_bus_instance.invoke(
                    AccepterTheseParScebCommand(
                        uuid_parcours_doctoral=self.parcours_doctoral_uuid,
                        matricule_sceb=self.request.user.person.global_id,
                        commentaire_interne=form.cleaned_data['commentaire_interne'],
                        commentaire_externe=form.cleaned_data['commentaire_externe'],
                    )
                )

    def get_success_url(self):
        return resolve_url('parcours_doctoral:manuscript-validation', uuid=self.parcours_doctoral_uuid)
