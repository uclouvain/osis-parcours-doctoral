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
from django.conf import settings
from django.utils.translation import override
from django.views.generic import FormView

from base.utils.htmx import HtmxPermissionRequiredMixin
from osis_common.utils.htmx import HtmxMixin
from parcours_doctoral.forms.cdd.generic_send_mail import BaseEmailTemplateForm
from parcours_doctoral.utils.mail_templates import get_email_template
from parcours_doctoral.views.mixins import (
    BusinessExceptionFormViewMixin,
    ParcoursDoctoralFormMixin,
)


class BaseEmailFormView(
    HtmxPermissionRequiredMixin,
    HtmxMixin,
    BusinessExceptionFormViewMixin,
    ParcoursDoctoralFormMixin,
    FormView,
):
    """
    View to open a modal containing two form fields to edit an email whose identifier is specified with the
    email_identifier attribute. The subject and the body of the email can be retrieved in the form_valid or
    call_command methods through the form.cleaned_data parameter. Only the version in the language returned by
    the method get_language is used here (by default the student language).
    """

    form_class = BaseEmailTemplateForm
    template_name = 'parcours_doctoral/includes/htmx_form_modal.html'
    htmx_template_name = 'parcours_doctoral/includes/htmx_form_modal.html'
    email_identifier = ''
    load_doctorate_dto = False
    disabled_form = False

    def get_tokens(self):
        """Returns a dictionary containing the computed tokens to display in the email."""
        return {}

    def get_language(self):
        """Returns the language in which the email is displayed."""
        return self.parcours_doctoral.student.language

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['disabled_form'] = self.disabled_form
        return form_kwargs

    def get_initial(self):
        current_language = self.get_language() or settings.LANGUAGE_CODE

        mail_template = get_email_template(
            identifier=self.email_identifier,
            language=current_language,
            management_entity_id=self.parcours_doctoral.training.management_entity_id,
        )

        if not mail_template:
            return {}

        with override(current_language):
            tokens = self.get_tokens()

            return {
                'subject': mail_template.render_subject(tokens),
                'body': mail_template.body_as_html(tokens),
            }
