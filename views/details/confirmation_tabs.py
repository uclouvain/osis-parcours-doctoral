# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import override
from django.views import View
from django.views.generic import FormView
from django.views.generic.edit import FormMixin
from osis_mail_template.models import MailTemplate

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from infrastructure.messages_bus import message_bus_instance
from osis_common.utils.htmx import HtmxMixin
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.epreuve_confirmation.commands import (
    ConfirmerEchecCommand,
    ConfirmerRepassageCommand,
    ConfirmerReussiteCommand,
    TeleverserAvisRenouvellementMandatRechercheCommand,
)
from parcours_doctoral.forms.cdd.generic_send_mail import (
    BaseEmailTemplateForm,
    SelectCddEmailTemplateForm,
)
from parcours_doctoral.forms.confirmation import (
    ConfirmationOpinionForm,
    ConfirmationRetakingForm,
)
from parcours_doctoral.infrastructure.parcours_doctoral.epreuve_confirmation.domain.service.notification import (
    Notification,
)
from parcours_doctoral.mail_templates.confirmation_paper import (
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_STUDENT,
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_STUDENT,
)
from parcours_doctoral.models.cdd_mail_template import CddMailTemplate
from parcours_doctoral.views.mixins import (
    BusinessExceptionFormViewMixin,
    LastConfirmationMixin,
)

__all__ = [
    "ConfirmationFailureDecisionView",
    "ConfirmationRetakingDecisionView",
    "ConfirmationSuccessDecisionView",
    "ConfirmationOpinionFormView",
]
__namespace__ = 'confirmation'


class ConfirmationSuccessDecisionView(
    LastConfirmationMixin,
    View,
):
    urlpatterns = 'success'
    permission_required = 'parcours_doctoral.make_confirmation_decision'

    def post(self, *args, **kwargs):
        try:
            message_bus_instance.invoke(ConfirmerReussiteCommand(uuid=self.last_confirmation_paper.uuid))
            messages.success(
                self.request,
                _("The status has been changed to %(status)s.")
                % {'status': _(ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE.value)},
            )
            messages.success(
                self.request,
                _('The certificate of achievement is being generated.'),
            )
        except MultipleBusinessExceptions as multiple_exceptions:
            for exception in multiple_exceptions.exceptions:
                messages.error(self.request, exception.message)

        return HttpResponseRedirect(reverse('parcours_doctoral:confirmation', args=[self.parcours_doctoral_uuid]))


class ConfirmationDecisionMixin(
    HtmxMixin,
    LastConfirmationMixin,
    BusinessExceptionFormViewMixin,
    FormMixin,
):
    permission_required = 'parcours_doctoral.make_confirmation_decision'
    htmx_template_name = 'parcours_doctoral/forms/send_mail_htmx_fields.html'
    template_name = 'parcours_doctoral/forms/confirmation_decision.html'
    identifier = ''
    page_title = ''

    def get_initial(self):
        mail_identifier = self.request.GET.get('template')

        tokens = Notification.get_common_tokens(self.parcours_doctoral, self.last_confirmation_paper)

        if mail_identifier and mail_identifier.isnumeric():
            # Template is a custom one
            mail_template = CddMailTemplate.objects.get(
                pk=mail_identifier,
                cdd=self.parcours_doctoral.training.management_entity,
            )
        else:
            # Template is the generic one
            mail_template = MailTemplate.objects.get(
                identifier=self.identifier,
                language=self.parcours_doctoral.student.language,
            )

        with override(language=self.parcours_doctoral.student.language):
            return {
                'subject': mail_template.render_subject(tokens),
                'body': mail_template.body_as_html(tokens),
            }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.htmx:
            return context

        context['select_template_form'] = SelectCddEmailTemplateForm(
            identifier=self.identifier,
            parcours_doctoral=self.parcours_doctoral,
            initial={
                'template': self.request.GET.get('template'),
            },
        )

        context['page_title'] = self.page_title
        context['submit_label'] = _('Confirm and send the message')

        return context

    def get_success_url(self):
        return reverse('parcours_doctoral:confirmation', args=[self.parcours_doctoral_uuid])


class ConfirmationFailureDecisionView(
    ConfirmationDecisionMixin,
    FormView,
):
    urlpatterns = 'failure'
    form_class = BaseEmailTemplateForm
    identifier = PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_STUDENT
    page_title = _('Failure of the confirmation paper')
    message_on_success = _("The status has been changed to %(status)s.") % {
        'status': _(ChoixStatutParcoursDoctoral.NON_AUTORISE_A_POURSUIVRE.value)
    }

    def call_command(self, form):
        message_bus_instance.invoke(
            ConfirmerEchecCommand(
                uuid=self.last_confirmation_paper.uuid,
                sujet_message=form.cleaned_data['subject'],
                corps_message=form.cleaned_data['body'],
            )
        )


class ConfirmationRetakingDecisionView(
    ConfirmationDecisionMixin,
    FormView,
):
    urlpatterns = 'retaking'
    form_class = ConfirmationRetakingForm
    identifier = PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_STUDENT
    page_title = _('Retaking of the confirmation paper')
    message_on_success = _("The status has been changed to %(status)s.") % {
        'status': _(ChoixStatutParcoursDoctoral.CONFIRMATION_A_REPRESENTER.value)
    }

    def call_command(self, form):
        message_bus_instance.invoke(
            ConfirmerRepassageCommand(
                uuid=self.last_confirmation_paper.uuid,
                sujet_message=form.cleaned_data['subject'],
                corps_message=form.cleaned_data['body'],
                date_limite=form.cleaned_data['date_limite'],
            )
        )


class ConfirmationOpinionFormView(
    LastConfirmationMixin,
    BusinessExceptionFormViewMixin,
    FormView,
):
    urlpatterns = 'opinion'
    template_name = 'parcours_doctoral/forms/confirmation_opinion.html'
    form_class = ConfirmationOpinionForm
    permission_required = 'parcours_doctoral.upload_pdf_confirmation'

    def get_initial(self):
        return {
            'avis_renouvellement_mandat_recherche': self.last_confirmation_paper.avis_renouvellement_mandat_recherche,
        }

    def call_command(self, form):
        # Save the confirmation paper
        message_bus_instance.invoke(
            TeleverserAvisRenouvellementMandatRechercheCommand(
                uuid=self.last_confirmation_paper.uuid,
                **form.cleaned_data,
            )
        )

    def get_success_url(self):
        return reverse('parcours_doctoral:confirmation', args=[self.parcours_doctoral_uuid])
