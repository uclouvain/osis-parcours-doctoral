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
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy
from django.views import View

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.defense_privee.commands import AutoriserDefensePriveeCommand
from parcours_doctoral.views.mixins import ParcoursDoctoralBaseViewMixin

__namespace__ = 'private-defense'


__all__ = [
    "PrivateDefenseAuthorisationView",
    "PrivateDefenseSuccessView",
]


class PrivateDefenseAuthorisationView(ParcoursDoctoralBaseViewMixin, View):
    urlpatterns = 'authorise'
    permission_required = 'parcours_doctoral.authorise_private_defense'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        message_bus_instance.invoke(
            AutoriserDefensePriveeCommand(
                parcours_doctoral_uuid=self.parcours_doctoral_uuid,
                matricule_auteur=self.request.user.person.global_id,
            ),
        )

        messages.success(
            request=request,
            message=gettext_lazy('The private defense has been authorised.'),
        )

        return redirect('parcours_doctoral:private-defense', uuid=self.parcours_doctoral_uuid)


class PrivateDefenseSuccessView(View):
    urlpatterns = 'success'
