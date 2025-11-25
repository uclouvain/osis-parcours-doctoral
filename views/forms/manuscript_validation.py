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

from django.utils.translation import gettext_lazy
from django.views.generic import FormView

from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.autorisation_diffusion_these.commands import (
    AccepterTheseParAdreCommand,
    AccepterTheseParScebCommand,
    RefuserTheseParAdreCommand,
    RefuserTheseParScebCommand,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.enums import (
    CHOIX_STATUTS_AUTORISATION_DIFFUSION_THESE_MODIFIABLE_PAR_ADRE,
    CHOIX_STATUTS_AUTORISATION_DIFFUSION_THESE_MODIFIABLE_PAR_SCEB,
    ChoixEtatSignature,
    ChoixStatutAutorisationDiffusionThese,
)
from parcours_doctoral.forms.manuscript_validation import (
    ManuscriptValidationApprovalForm,
)
from parcours_doctoral.views.details.manuscript_validation import (
    ManuscriptValidationCommonViewMixin,
)
from parcours_doctoral.views.mixins import (
    BusinessExceptionFormViewMixin,
    ParcoursDoctoralFormMixin,
)

__all__ = [
    'ManuscriptValidationApprovalFormView',
]

__namespace__ = False


class ManuscriptValidationApprovalFormView(
    ManuscriptValidationCommonViewMixin,
    ParcoursDoctoralFormMixin,
    BusinessExceptionFormViewMixin,
    FormView,
):
    urlpatterns = 'manuscript-validation'
    template_name = 'parcours_doctoral/forms/manuscript_validation.html'
    permission_required = 'parcours_doctoral.validate_manuscript'
    form_class = ManuscriptValidationApprovalForm
    extra_context = {'submit_label': gettext_lazy('Submit my decision')}

    def call_command(self, form):
        decision = form.cleaned_data.get('decision', None)

        authorization_distribution = self.authorization_distribution

        if authorization_distribution.statut in CHOIX_STATUTS_AUTORISATION_DIFFUSION_THESE_MODIFIABLE_PAR_ADRE:
            if decision == ChoixEtatSignature.DECLINED.name:
                message_bus_instance.invoke(
                    RefuserTheseParAdreCommand(
                        uuid_parcours_doctoral=self.parcours_doctoral_uuid,
                        matricule_adre=self.request.user.person.global_id,
                        motif_refus=form.cleaned_data['motif_refus'],
                        commentaire_interne=form.cleaned_data['commentaire_interne'],
                        commentaire_externe=form.cleaned_data['commentaire_externe'],
                    )
                )
            elif decision == ChoixEtatSignature.APPROVED.name:
                message_bus_instance.invoke(
                    AccepterTheseParAdreCommand(
                        uuid_parcours_doctoral=self.parcours_doctoral_uuid,
                        matricule_adre=self.request.user.person.global_id,
                        commentaire_interne=form.cleaned_data['commentaire_interne'],
                        commentaire_externe=form.cleaned_data['commentaire_externe'],
                    )
                )

        elif authorization_distribution.statut in CHOIX_STATUTS_AUTORISATION_DIFFUSION_THESE_MODIFIABLE_PAR_SCEB:
            if decision == ChoixEtatSignature.DECLINED.name:
                message_bus_instance.invoke(
                    RefuserTheseParScebCommand(
                        uuid_parcours_doctoral=self.parcours_doctoral_uuid,
                        matricule_sceb=self.request.user.person.global_id,
                        motif_refus=form.cleaned_data['motif_refus'],
                        commentaire_interne=form.cleaned_data['commentaire_interne'],
                        commentaire_externe=form.cleaned_data['commentaire_externe'],
                    )
                )
            elif decision == ChoixEtatSignature.APPROVED.name:
                message_bus_instance.invoke(
                    AccepterTheseParScebCommand(
                        uuid_parcours_doctoral=self.parcours_doctoral_uuid,
                        matricule_sceb=self.request.user.person.global_id,
                        commentaire_interne=form.cleaned_data['commentaire_interne'],
                        commentaire_externe=form.cleaned_data['commentaire_externe'],
                    )
                )
