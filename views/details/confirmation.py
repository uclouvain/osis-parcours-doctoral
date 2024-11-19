# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from typing import List

from django.http import Http404
from django.views.generic import TemplateView

from parcours_doctoral.ddd.domain.validator.exceptions import ParcoursDoctoralNonTrouveException
from parcours_doctoral.ddd.epreuve_confirmation.commands import RecupererEpreuvesConfirmationQuery
from parcours_doctoral.ddd.epreuve_confirmation.dtos import EpreuveConfirmationDTO
from parcours_doctoral.mail_templates.confirmation_paper import PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT
from parcours_doctoral.views.mixins import ParcoursDoctoralViewMixin
from infrastructure.messages_bus import message_bus_instance

__all__ = [
    "ConfirmationDetailView",
]


class ConfirmationDetailView(ParcoursDoctoralViewMixin, TemplateView):
    template_name = 'parcours_doctoral/details/confirmation.html'
    permission_required = 'parcours_doctoral.view_confirmation'
    mandatory_fields_for_evaluation = [
        'date',
        'proces_verbal_ca',
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            all_confirmation_papers: List[EpreuveConfirmationDTO] = message_bus_instance.invoke(
                RecupererEpreuvesConfirmationQuery(parcours_doctoral_uuid=self.parcours_doctoral_uuid),
            )
        except ParcoursDoctoralNonTrouveException as e:
            raise Http404(e.message)

        if all_confirmation_papers:
            current_confirmation_paper = all_confirmation_papers.pop(0)
            context['can_be_evaluated'] = all(
                getattr(current_confirmation_paper, field) for field in self.mandatory_fields_for_evaluation
            )
            context['current_confirmation_paper'] = current_confirmation_paper

        context['previous_confirmation_papers'] = all_confirmation_papers
        context['INFO_TEMPLATE_IDENTIFIER'] = PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT

        return context
