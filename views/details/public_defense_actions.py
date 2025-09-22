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
from parcours_doctoral.ddd.soutenance_publique.commands import (
    InviterJurySoutenancePubliqueCommand,
)
from parcours_doctoral.infrastructure.parcours_doctoral.soutenance_publique.domain.service.notification import (
    Notification,
)
from parcours_doctoral.mail_templates.public_defense import (
    PARCOURS_DOCTORAL_EMAIL_PUBLIC_DEFENSE_JURY_INVITATION,
)
from parcours_doctoral.views.email_mixin import BaseEmailFormView

__namespace__ = 'public-defense'


__all__ = [
    "PublicDefenseJuryInvitationView",
    "PublicDefenseSuccessView",
]


class BasePublicDefenseActionView(BaseEmailFormView):
    def get_tokens(self):
        doctorate = Notification.get_doctorate(doctorate_uuid=self.parcours_doctoral_uuid)
        return Notification.get_common_tokens(
            doctorate=doctorate,
            sender_first_name=self.request.user.person.first_name,
            sender_last_name=self.request.user.person.last_name,
        )

    def get_success_url(self):
        return resolve_url('parcours_doctoral:public-defense', uuid=self.parcours_doctoral_uuid)


class PublicDefenseJuryInvitationView(BasePublicDefenseActionView):
    urlpatterns = 'jury-invitation'
    permission_required = 'parcours_doctoral.invite_jury_to_public_defense'
    message_on_success = gettext_lazy('The members of the jury have been invited to the public defense.')
    email_identifier = PARCOURS_DOCTORAL_EMAIL_PUBLIC_DEFENSE_JURY_INVITATION
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
        message_bus_instance.invoke(
            InviterJurySoutenancePubliqueCommand(
                parcours_doctoral_uuid=self.parcours_doctoral_uuid,
                matricule_auteur=self.request.user.person.global_id,
            )
        )


class PublicDefenseSuccessView(BasePublicDefenseActionView):
    urlpatterns = 'success'
