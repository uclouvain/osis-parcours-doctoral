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
from django.utils.translation import gettext_lazy

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.defense_privee.commands import (
    AutoriserDefensePriveeCommand,
    ConfirmerEchecDefensePriveeCommand,
    ConfirmerReussiteDefensePriveeCommand,
    InviterJuryDefensePriveeCommand,
)
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.infrastructure.parcours_doctoral.defense_privee.domain.service.notification import (
    Notification,
)
from parcours_doctoral.mail_templates.private_defense import (
    PARCOURS_DOCTORAL_EMAIL_PRIVATE_DEFENSE_AUTHORISATION,
    PARCOURS_DOCTORAL_EMAIL_PRIVATE_DEFENSE_JURY_INVITATION,
    PARCOURS_DOCTORAL_EMAIL_PRIVATE_DEFENSE_ON_FAILURE,
    PARCOURS_DOCTORAL_EMAIL_PRIVATE_DEFENSE_ON_SUCCESS,
)
from parcours_doctoral.views.email_mixin import BaseEmailFormView

__namespace__ = 'private-defense'


__all__ = [
    "PrivateDefenseAuthorisationView",
    "PrivateDefenseFailureView",
    "PrivateDefenseJuryInvitationView",
    "PrivateDefenseSuccessView",
]


class BasePrivateDefenseActionView(BaseEmailFormView):
    def get_tokens(self):
        doctorate = Notification.get_doctorate(doctorate_uuid=self.parcours_doctoral_uuid)
        return Notification.get_common_tokens(
            doctorate=doctorate,
            sender_first_name=self.request.user.person.first_name,
            sender_last_name=self.request.user.person.last_name,
        )

    def get_success_url(self):
        return resolve_url('parcours_doctoral:private-defense', uuid=self.parcours_doctoral_uuid)


class PrivateDefenseAuthorisationView(BasePrivateDefenseActionView):
    urlpatterns = 'authorise'
    permission_required = 'parcours_doctoral.authorise_private_defense'
    message_on_success = gettext_lazy('The private defense has been authorised.')
    email_identifier = PARCOURS_DOCTORAL_EMAIL_PRIVATE_DEFENSE_AUTHORISATION

    def call_command(self, form):
        message_bus_instance.invoke(
            AutoriserDefensePriveeCommand(
                parcours_doctoral_uuid=self.parcours_doctoral_uuid,
                matricule_auteur=self.request.user.person.global_id,
                sujet_message=form.cleaned_data['subject'],
                corps_message=form.cleaned_data['body'],
            ),
        )

        self.htmx_refresh = True


class PrivateDefenseJuryInvitationView(BasePrivateDefenseActionView):
    urlpatterns = 'jury-invitation'
    permission_required = 'parcours_doctoral.invite_jury_to_private_defense'
    message_on_success = gettext_lazy('The members of the jury have been invited to the private defense.')
    email_identifier = PARCOURS_DOCTORAL_EMAIL_PRIVATE_DEFENSE_JURY_INVITATION
    disabled_form = True

    def get_language(self):
        return self.request.user.person.language

    def get_tokens(self):
        tokens = super().get_tokens()

        # Examples as the mail will be generated
        tokens['jury_member_first_name'] = 'John'
        tokens['jury_member_last_name'] = 'Doe'

        return tokens

    def call_command(self, form):
        message_bus_instance.invoke(
            InviterJuryDefensePriveeCommand(
                parcours_doctoral_uuid=self.parcours_doctoral_uuid,
                matricule_auteur=self.request.user.person.global_id,
            )
        )
        self.htmx_refresh = True


class PrivateDefenseSuccessView(BasePrivateDefenseActionView):
    urlpatterns = 'success'
    permission_required = 'parcours_doctoral.make_private_defense_decision'
    email_identifier = PARCOURS_DOCTORAL_EMAIL_PRIVATE_DEFENSE_ON_SUCCESS

    def call_command(self, form):
        message_bus_instance.invoke(
            ConfirmerReussiteDefensePriveeCommand(
                parcours_doctoral_uuid=self.parcours_doctoral_uuid,
                matricule_auteur=self.request.user.person.global_id,
                sujet_message=form.cleaned_data['subject'],
                corps_message=form.cleaned_data['body'],
            )
        )
        self.message_on_success = gettext_lazy('The status has been changed to %(status)s.') % {
            'status': ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_REUSSIE.value
        }
        self.htmx_refresh = True


class PrivateDefenseFailureView(BasePrivateDefenseActionView):
    urlpatterns = 'failure'
    permission_required = 'parcours_doctoral.make_private_defense_decision'
    email_identifier = PARCOURS_DOCTORAL_EMAIL_PRIVATE_DEFENSE_ON_FAILURE

    def call_command(self, form):
        message_bus_instance.invoke(
            ConfirmerEchecDefensePriveeCommand(
                parcours_doctoral_uuid=self.parcours_doctoral_uuid,
                matricule_auteur=self.request.user.person.global_id,
                sujet_message=form.cleaned_data['subject'],
                corps_message=form.cleaned_data['body'],
            )
        )
        self.message_on_success = gettext_lazy('The status has been changed to %(status)s.') % {
            'status': ChoixStatutParcoursDoctoral.NON_AUTORISE_A_POURSUIVRE.value
        }
        self.htmx_refresh = True
