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

from base.forms.utils.datefield import CustomDateInput
from osis_document.contrib import FileUploadField


class ExtensionRequestOpinionForm(forms.Form):
    avis_cdd = forms.CharField(
        label=_('CDD opinion'),
        required=True,
        widget=forms.Textarea(),
    )


class ExtensionRequestForm(forms.Form):
    nouvelle_echeance = forms.DateField(
        label=_('Proposed new deadline'),
        required=True,
        widget=CustomDateInput(),
    )
    justification_succincte = forms.CharField(
        label=_('Brief justification'),
        required=True,
        max_length=2000,
        widget=forms.Textarea(),
    )
    lettre_justification = FileUploadField(
        label=_('Justification letter'),
        required=False,
        help_text=_(
            'If applicable, please upload here the opinion of your support committee on the extension request.',
        ),
    )
