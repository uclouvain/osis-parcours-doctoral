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
from dal import autocomplete
from django import forms
from django.utils.translation import gettext_lazy as _

from admission.utils import get_language_initial_choices
from osis_profile.forms import DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS
from parcours_doctoral.ddd.jury.domain.model.enums import FormuleDefense
from parcours_doctoral.forms.project import LANGUAGE_UNDECIDED


class JuryPreparationForm(forms.Form):
    titre_propose = forms.CharField(
        label=_("Proposed thesis title"),
        help_text=_("This is a temporary title and it will be modifiable later depending on the jury analysis."),
        required=False,
    )
    formule_defense = forms.ChoiceField(
        label=_("Defense method"),
        help_text=_(
            "Refer to the specific measures of your doctoral commission to know if one of these method is "
            "mandatory to you."
        ),
        choices=FormuleDefense.choices(),
        widget=forms.RadioSelect(),
        initial=FormuleDefense.FORMULE_1.name,
        required=False,
    )
    date_indicative = forms.CharField(
        label=_("Anticipated date or period for private defence (Format 1) or admissibility (Format 2)"),
        required=False,
    )
    langue_redaction = forms.CharField(
        label=_("Thesis language"),
        required=True,
        widget=autocomplete.ListSelect2(
            url="language-autocomplete",
            attrs={
                **DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS,
            },
        ),
    )
    langue_soutenance = forms.CharField(
        label=_("Defense language"),
        required=False,
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:language",
            attrs={
                **DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS,
            },
        ),
    )
    commentaire = forms.CharField(
        label=_("Comment"),
        widget=forms.Textarea(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize the fields with dynamic choices
        def initialize_lang_field(field_name):
            lang_code = self.data.get(self.add_prefix(field_name), self.initial.get(field_name))

            if lang_code == LANGUAGE_UNDECIDED:
                choices = ((LANGUAGE_UNDECIDED, _('Undecided')),)
            else:
                choices = get_language_initial_choices(lang_code)

            self.fields[field_name].widget.choices = choices
            self.fields[field_name].choices = choices

        initialize_lang_field('langue_redaction')
        initialize_lang_field('langue_redaction')
