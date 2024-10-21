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
from base.forms.utils.datefield import CustomDateInput
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from osis_document.contrib import FileUploadField

from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.forms.cdd.generic_send_mail import BaseEmailTemplateForm


class ConfirmationOpinionForm(forms.Form):
    avis_renouvellement_mandat_recherche = FileUploadField(
        label=_('Opinion on research mandate renewal'),
        required=False,
        max_files=1,
    )


class ConfirmationForm(ConfirmationOpinionForm):
    date_limite = forms.DateField(
        label=_('Confirmation deadline'),
        required=True,
        widget=CustomDateInput(),
    )
    date = forms.DateField(
        label=_('Confirmation exam date'),
        required=True,
        widget=CustomDateInput(),
    )
    rapport_recherche = FileUploadField(
        label=_('Research report'),
        required=False,
        max_files=1,
    )
    proces_verbal_ca = FileUploadField(
        label=_('Support Committee minutes'),
        required=False,
        max_files=1,
    )

    def __init__(self, parcours_doctoral_status=None, **kwargs):
        super().__init__(**kwargs)
        if parcours_doctoral_status == ChoixStatutParcoursDoctoral.ADMITTED.name:
            self.fields['date'].required = False

    def clean(self):
        cleaned_data = super().clean()

        # Check dates
        date = cleaned_data.get('date')
        deadline = cleaned_data.get('date_limite')

        if date and deadline and date > deadline:
            raise ValidationError(_('The date of the confirmation paper cannot be later than its deadline.'))

        return cleaned_data

    class Media:
        js = [
            'js/jquery.mask.min.js',
        ]


class ConfirmationRetakingForm(BaseEmailTemplateForm):
    date_limite = forms.DateField(
        label=_('Confirmation deadline'),
        required=True,
        widget=CustomDateInput(),
    )

    class Media:
        js = [
            'js/jquery.mask.min.js',
        ]
