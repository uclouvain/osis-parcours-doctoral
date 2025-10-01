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
from django import forms
from django.utils.translation import gettext_lazy as _

from parcours_doctoral.ddd.jury.domain.model.enums import DecisionApprovalEnum


class JuryApprovalForm(forms.Form):
    decision = forms.ChoiceField(
        label=_("Decision"),
        choices=DecisionApprovalEnum.choices(),
        widget=forms.RadioSelect,
        required=True,
    )
    motif_refus = forms.CharField(
        label=_('Grounds for denied'),
        required=False,
        max_length=50,
    )
    commentaire_interne = forms.CharField(
        label=_('Internal comment'),
        required=False,
        widget=forms.Textarea(
            attrs={
                'rows': 5,
            },
        ),
        help_text=_("This comment will be visible only to administrators."),
    )
    commentaire_externe = forms.CharField(
        label=_('Comment for the candidate'),
        required=False,
        widget=forms.Textarea(
            attrs={
                'rows': 5,
            },
        ),
        help_text=_("This comment will be visible to all users with access to the jury."),
    )

    def clean(self):
        data = super().clean()
        if data.get('decision') == DecisionApprovalEnum.DECLINED.name and not data.get('motif_refus'):
            self.add_error('motif_refus', _("This field is required."))

    class Media:
        js = ('js/dependsOn.min.js',)
