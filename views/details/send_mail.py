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

from django.forms import BaseForm
from django.utils.translation import gettext_lazy as _
from django.utils.translation import override
from django.views.generic import FormView
from osis_common.utils.htmx import HtmxMixin
from osis_mail_template.models import MailTemplate

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.commands import EnvoyerMessageDoctorantCommand
from parcours_doctoral.forms.send_mail import SendMailForm
from parcours_doctoral.infrastructure.parcours_doctoral.domain.service.notification import (
    Notification,
)
from parcours_doctoral.mail_templates import PARCOURS_DOCTORAL_EMAIL_GENERIC
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(self.get_extra_form_kwargs())
        return kwargs

    def get_initial(self):
        mail_template = MailTemplate.objects.get(
            identifier=PARCOURS_DOCTORAL_EMAIL_GENERIC,
            language=self.parcours_doctoral.student.language,
        )
        tokens = Notification.get_common_tokens(self.parcours_doctoral)

        with override(language=self.parcours_doctoral.student.language):
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
