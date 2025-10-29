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

from django.forms import BaseForm
from django.utils.translation import gettext_lazy as _
from django.utils.translation import override
from django.views.generic import FormView

from infrastructure.messages_bus import message_bus_instance
from osis_common.utils.htmx import HtmxMixin
from parcours_doctoral.ddd.commands import EnvoyerMessageDoctorantCommand
from parcours_doctoral.forms.send_mail import SendMailForm
from parcours_doctoral.infrastructure.parcours_doctoral.domain.service.notification import (
    Notification,
)
from parcours_doctoral.infrastructure.parcours_doctoral.epreuve_confirmation.domain.service.notification import (
    Notification as NotificationEpreuveConfirmation,
)
from parcours_doctoral.infrastructure.parcours_doctoral.soutenance_publique.domain.service.notification import (
    Notification as NotificationSoutenancePublique,
)
from parcours_doctoral.mail_templates import (
    CONFIRMATION_PAPER_TEMPLATES_IDENTIFIERS,
    PARCOURS_DOCTORAL_EMAIL_GENERIC,
)
from parcours_doctoral.mail_templates.public_defense import (
    PUBLIC_DEFENSE_TEMPLATES_IDENTIFIERS,
)
from parcours_doctoral.models import CddMailTemplate
from parcours_doctoral.utils.mail_templates import get_email_template
from parcours_doctoral.views.mixins import ParcoursDoctoralFormMixin

__all__ = [
    "SendMailView",
]


class SendMailView(HtmxMixin, ParcoursDoctoralFormMixin, FormView):
    template_name = 'parcours_doctoral/forms/send_mail.html'
    htmx_template_name = 'parcours_doctoral/forms/send_mail_htmx.html'
    form_class = SendMailForm
    permission_required = 'parcours_doctoral.send_message'

    def get_success_url(self):
        return self.request.get_full_path()

    def get_extra_form_kwargs(self):
        return {
            'parcours_doctoral': self.parcours_doctoral,
        }

    def get_tokens(self, identifier):
        if identifier in CONFIRMATION_PAPER_TEMPLATES_IDENTIFIERS:
            return NotificationEpreuveConfirmation.get_common_tokens(
                self.parcours_doctoral,
                self.last_confirmation_paper,
            )
        elif identifier in PUBLIC_DEFENSE_TEMPLATES_IDENTIFIERS:
            return NotificationSoutenancePublique.get_common_tokens(
                NotificationSoutenancePublique.get_doctorate(self.parcours_doctoral_uuid),
                sender_first_name=self.request.user.person.first_name,
                sender_last_name=self.request.user.person.last_name,
            )
        return Notification.get_common_tokens(self.parcours_doctoral)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(self.get_extra_form_kwargs())
        return kwargs

    def get_initial(self):
        identifier = self.request.GET.get('template') or PARCOURS_DOCTORAL_EMAIL_GENERIC

        if identifier.isnumeric():
            # Template is a custom one
            mail_template = CddMailTemplate.objects.get(pk=identifier)
            identifier = mail_template.identifier
        else:
            # Template is a custom one if any, otherwise a generic one
            mail_template = get_email_template(
                identifier=identifier,
                language=self.parcours_doctoral.student.language,
                management_entity_id=self.parcours_doctoral.training.management_entity_id,
            )

        with override(language=self.parcours_doctoral.student.language):
            tokens = self.get_tokens(identifier)

            return {
                **self.request.GET,
                'subject': mail_template.render_subject(tokens),
                'body': mail_template.body_as_html(tokens),
            }

    def form_valid(self, form: BaseForm):
        message_bus_instance.invoke(
            EnvoyerMessageDoctorantCommand(
                matricule_emetteur=self.request.user.person.global_id,
                parcours_doctoral_uuid=self.parcours_doctoral.uuid,
                sujet=form.cleaned_data['subject'],
                message=form.cleaned_data['body'],
                cc_promoteurs=form.cleaned_data['cc_promoteurs'],
                cc_membres_ca=form.cleaned_data['cc_membres_ca'],
            )
        )
        self.message_on_success = _("Message sent successfully")
        return super().form_valid(self.form_class(**self.get_extra_form_kwargs()))
