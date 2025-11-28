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
from django.conf import settings
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from osis_document_components.forms import FileUploadField

from base.forms.utils import EMPTY_CHOICE
from base.forms.utils.autocomplete import ListSelect2
from base.forms.utils.datefield import CustomDateInput
from osis_profile.constants import JPEG_MIME_TYPE, PNG_MIME_TYPE
from parcours_doctoral.forms.fields import DoctorateDateTimeField
from reference.models.language import Language


class PublicDefenseForm(forms.Form):
    langue_soutenance_publique = forms.ChoiceField(
        label=_('Public defence language'),
        widget=ListSelect2,
        required=False,
    )

    date_heure_soutenance_publique = DoctorateDateTimeField(
        label=_('Public defence date and time'),
        help_text=_('The public defence takes place at least one month after the private defence.'),
        required=False,
    )

    lieu_soutenance_publique = forms.CharField(
        label=_('Public defence location'),
        required=False,
        max_length=255,
    )

    local_deliberation = forms.CharField(
        label=_('Deliberation room'),
        required=False,
        max_length=255,
    )

    informations_complementaires = forms.CharField(
        label=_('Additional information'),
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
    )

    resume_annonce = forms.CharField(
        label=_('Text for the poster'),
        widget=forms.Textarea(attrs={'rows': '2'}),
        required=False,
    )

    photo_annonce = FileUploadField(
        label=_('Photo for announcement'),
        max_files=1,
        mimetypes=[JPEG_MIME_TYPE, PNG_MIME_TYPE],
        required=False,
    )

    proces_verbal_soutenance_publique = FileUploadField(
        label=_('Public defence minutes'),
        help_text=_('The minutes will be uploaded by the thesis exam board secretary or chair.'),
        required=False,
    )

    date_retrait_diplome = forms.DateField(
        label=_('Diploma collection date'),
        widget=CustomDateInput(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Load dynamic choices
        language_name_field = 'name_en' if get_language() == settings.LANGUAGE_CODE_EN else 'name'
        choices = [EMPTY_CHOICE[0]]
        qs = Language.objects.order_by(language_name_field).values_list('code', language_name_field)
        choices.extend(qs)
        self.fields['langue_soutenance_publique'].choices = choices
