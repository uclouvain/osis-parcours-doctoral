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
from django.contrib import messages
from django.core.exceptions import NON_FIELD_ERRORS
from django.forms import Form
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.jury.commands import (
    ApprouverJuryParAdreCommand,
    ApprouverJuryParCddCommand,
    DemanderSignaturesCommand,
    ModifierJuryCommand,
    RefuserJuryParAdreCommand,
    RefuserJuryParCddCommand,
    ReinitialiserSignaturesCommand,
)
from parcours_doctoral.ddd.jury.domain.model.enums import DecisionApprovalEnum
from parcours_doctoral.forms.jury.approval import JuryApprovalForm
from parcours_doctoral.forms.jury.preparation import JuryPreparationForm
from parcours_doctoral.views.mixins import (
    BusinessExceptionFormViewMixin,
    ParcoursDoctoralViewMixin,
)

__all__ = [
    "JuryPreparationFormView",
    "JuryRequestSignaturesView",
    "JuryResetSignaturesView",
    "JuryCddDecisionView",
    "JuryAdreDecisionView",
]

__namespace__ = False


class JuryPreparationFormView(
    ParcoursDoctoralViewMixin,
    BusinessExceptionFormViewMixin,
    FormView,
):
    urlpatterns = 'jury-preparation'
    template_name = 'parcours_doctoral/forms/jury/preparation.html'
    permission_required = 'parcours_doctoral.change_jury'
    form_class = JuryPreparationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cotutelle'] = self.cotutelle
        return context

    def get_initial(self):
        return {
            'titre_propose': self.jury.titre_propose,
            'formule_defense': self.jury.formule_defense,
            'date_indicative': self.jury.date_indicative,
            'langue_redaction': self.jury.langue_redaction,
            'langue_soutenance': self.jury.langue_soutenance,
            'commentaire': self.jury.commentaire,
        }

    def call_command(self, form):
        message_bus_instance.invoke(
            ModifierJuryCommand(
                uuid_parcours_doctoral=self.parcours_doctoral_uuid,
                **form.cleaned_data,
            )
        )

    def get_success_url(self):
        return reverse('parcours_doctoral:jury-preparation', args=[self.parcours_doctoral_uuid])


class JuryRequestSignaturesView(ParcoursDoctoralViewMixin, BusinessExceptionFormViewMixin, FormView):
    urlpatterns = 'jury-request-signatures'
    form_class = Form
    permission_required = 'parcours_doctoral.jury_request_signatures'

    def form_invalid(self, form):
        for error in form.errors.get(NON_FIELD_ERRORS, []):
            messages.error(self.request, error)
        return redirect(self.get_success_url())

    def call_command(self, form):
        message_bus_instance.invoke(
            DemanderSignaturesCommand(
                uuid_parcours_doctoral=self.parcours_doctoral_uuid,
                matricule_auteur=self.request.user.person.global_id,
            )
        )

    def get_success_url(self):
        return reverse('parcours_doctoral:jury', args=[self.parcours_doctoral_uuid])


class JuryResetSignaturesView(ParcoursDoctoralViewMixin, BusinessExceptionFormViewMixin, FormView):
    urlpatterns = 'jury-reset-signatures'
    form_class = Form
    permission_required = 'parcours_doctoral.jury_reset_signatures'

    def form_invalid(self, form):
        for error in form.errors.get(NON_FIELD_ERRORS, []):
            messages.error(self.request, error)
        return redirect(self.get_success_url())

    def call_command(self, form):
        message_bus_instance.invoke(
            ReinitialiserSignaturesCommand(
                uuid_jury=self.parcours_doctoral_uuid,
                matricule_auteur=self.request.user.person.global_id,
            )
        )

    def get_success_url(self):
        return reverse('parcours_doctoral:jury', args=[self.parcours_doctoral_uuid])


class JuryCddDecisionView(ParcoursDoctoralViewMixin, BusinessExceptionFormViewMixin, FormView):
    urlpatterns = 'jury-cdd-decision'
    form_class = JuryApprovalForm
    permission_required = 'parcours_doctoral.approve_jury'

    def get_success_url(self):
        return reverse('parcours_doctoral:jury', args=[self.parcours_doctoral_uuid])

    def form_invalid(self, form):
        # Pass data and errors to JuryView
        self.request.session['jury_approval_data'] = form.data
        self.request.session['jury_approval_errors'] = form.errors
        return redirect(self.get_success_url())

    def call_command(self, form):
        decision = form.cleaned_data['decision']
        if decision == DecisionApprovalEnum.APPROVED.name:
            return message_bus_instance.invoke(
                ApprouverJuryParCddCommand(
                    uuid_jury=self.parcours_doctoral_uuid,
                    matricule_auteur=self.request.user.person.global_id,
                    commentaire_interne=form.cleaned_data.get('commentaire_interne'),
                    commentaire_externe=form.cleaned_data.get('commentaire_externe'),
                )
            )
        return message_bus_instance.invoke(
            RefuserJuryParCddCommand(
                uuid_jury=self.parcours_doctoral_uuid,
                matricule_auteur=self.request.user.person.global_id,
                motif_refus=form.cleaned_data.get('motif_refus'),
                commentaire_interne=form.cleaned_data.get('commentaire_interne'),
                commentaire_externe=form.cleaned_data.get('commentaire_externe'),
            )
        )


class JuryAdreDecisionView(ParcoursDoctoralViewMixin, BusinessExceptionFormViewMixin, FormView):
    urlpatterns = 'jury-adre-decision'
    form_class = JuryApprovalForm
    permission_required = 'parcours_doctoral.approve_jury'

    def get_success_url(self):
        return reverse('parcours_doctoral:jury', args=[self.parcours_doctoral_uuid])

    def form_invalid(self, form):
        # Pass data and errors to JuryView
        self.request.session['jury_approval_data'] = form.data
        self.request.session['jury_approval_errors'] = form.errors
        return redirect(self.get_success_url())

    def call_command(self, form):
        decision = form.cleaned_data['decision']
        if decision == DecisionApprovalEnum.APPROVED.name:
            return message_bus_instance.invoke(
                ApprouverJuryParAdreCommand(
                    uuid_jury=self.parcours_doctoral_uuid,
                    matricule_auteur=self.request.user.person.global_id,
                    commentaire_interne=form.cleaned_data.get('commentaire_interne'),
                    commentaire_externe=form.cleaned_data.get('commentaire_externe'),
                )
            )
        return message_bus_instance.invoke(
            RefuserJuryParAdreCommand(
                uuid_jury=self.parcours_doctoral_uuid,
                matricule_auteur=self.request.user.person.global_id,
                motif_refus=form.cleaned_data.get('motif_refus'),
                commentaire_interne=form.cleaned_data.get('commentaire_interne'),
                commentaire_externe=form.cleaned_data.get('commentaire_externe'),
            )
        )
