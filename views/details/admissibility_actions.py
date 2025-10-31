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
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.recevabilite.commands import (
    ConfirmerReussiteRecevabiliteCommand,
    InviterJuryRecevabiliteCommand,
)
from parcours_doctoral.infrastructure.parcours_doctoral.recevabilite.domain.service.notification import (
    Notification,
)
from parcours_doctoral.mail_templates.admissibility import (
    PARCOURS_DOCTORAL_EMAIL_ADMISSIBILITY_JURY_INVITATION,
    PARCOURS_DOCTORAL_EMAIL_ADMISSIBILITY_ON_SUCCESS,
)
from parcours_doctoral.views.email_mixin import BaseEmailFormView

__namespace__ = 'admissibility'


__all__ = [
    "AdmissibilityJuryInvitationView",
    "AdmissibilitySuccessView",
]


class BaseAdmissibilityActionView(BaseEmailFormView):
    def get_tokens(self):
        doctorate = Notification.get_doctorate(doctorate_uuid=self.parcours_doctoral_uuid)
        jury_members = Notification.get_jury_members(jury_group_id=doctorate.jury_group_id)
        return Notification.get_common_tokens(
            doctorate=doctorate,
            jury_members=jury_members,
        )

    def get_success_url(self):
        return resolve_url('parcours_doctoral:admissibility', uuid=self.parcours_doctoral_uuid)


class AdmissibilityJuryInvitationView(BaseAdmissibilityActionView):
    urlpatterns = 'jury-invitation'
    permission_required = 'parcours_doctoral.invite_jury_to_admissibility'
    message_on_success = gettext_lazy('The members of the jury have been invited to the admissibility.')
    email_identifier = PARCOURS_DOCTORAL_EMAIL_ADMISSIBILITY_JURY_INVITATION
    disabled_form = True
    prefix = 'jury-invitation'

    def get_language(self):
        return self.request.user.person.language

    def get_tokens(self):
        tokens = super().get_tokens()

        # Examples as the mail will be generated
        tokens['jury_member_first_name'] = 'John'
        tokens['jury_member_last_name'] = 'Doe'

        return tokens

    def call_command(self, form):
        message_bus_instance.invoke(InviterJuryRecevabiliteCommand(parcours_doctoral_uuid=self.parcours_doctoral_uuid))


class AdmissibilitySuccessView(BaseAdmissibilityActionView):
    urlpatterns = 'success'
    permission_required = 'parcours_doctoral.make_admissibility_decision'
    email_identifier = PARCOURS_DOCTORAL_EMAIL_ADMISSIBILITY_ON_SUCCESS
    prefix = 'success'

    def call_command(self, form):
        message_bus_instance.invoke(
            ConfirmerReussiteRecevabiliteCommand(
                parcours_doctoral_uuid=self.parcours_doctoral_uuid,
                matricule_auteur=self.request.user.person.global_id,
                sujet_message=form.cleaned_data['subject'],
                corps_message=form.cleaned_data['body'],
            )
        )
        self.message_on_success = gettext_lazy('The status has been changed to %(status)s.') % {
            'status': ChoixStatutParcoursDoctoral.RECEVABILITE_REUSSIE.value
        }
        self.htmx_refresh = True
