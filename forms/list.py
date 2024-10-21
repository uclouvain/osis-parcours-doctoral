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
import re

from admission.forms import DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS
from base.forms.utils import autocomplete
from base.forms.widgets import Select2MultipleCheckboxesWidget
from base.models.person import Person
from base.templatetags.pagination_bs5 import DEFAULT_PAGINATOR_SIZE, PAGINATOR_SIZE_LIST
from django import forms
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext, pgettext_lazy

from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral

REGEX_REFERENCE = r'\d{4}\.\d{4}$'


class ParcoursDoctorauxFilterForm(forms.Form):
    numero = forms.RegexField(
        label=_('Doctoral training numero'),
        regex=re.compile(REGEX_REFERENCE),
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'L-ESPO22-0001.2345',
            },
        ),
    )

    noma = forms.RegexField(
        required=False,
        label=_('Noma'),
        regex=re.compile(r'^\d{8}$'),
        widget=forms.TextInput(
            attrs={
                "data-mask": "00000000",
            },
        ),
    )

    matricule_etudiant = forms.CharField(
        label=_('Last name / First name / Email'),
        required=False,
        widget=autocomplete.ListSelect2(
            url="parcours_doctoral:autocomplete:students",
            attrs=DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS,
        ),
    )

    formation = forms.CharField(
        label=pgettext_lazy('parcours_doctoral', 'Course'),
        required=False,
    )

    etats = forms.MultipleChoiceField(
        choices=ChoixStatutParcoursDoctoral.choices(),
        initial=ChoixStatutParcoursDoctoral.get_names(),
        label=_('Application status'),
        required=False,
        widget=Select2MultipleCheckboxesWidget(
            attrs={
                'data-dropdown-auto-width': True,
                'data-selection-template': _("{items} types out of {total}"),
            }
        ),
    )

    taille_page = forms.TypedChoiceField(
        label=_("Page size"),
        choices=((size, size) for size in PAGINATOR_SIZE_LIST),
        widget=forms.Select(attrs={'form': 'search_form', 'autocomplete': 'off'}),
        help_text=_("items per page"),
        required=False,
        initial=DEFAULT_PAGINATOR_SIZE,
        coerce=int,
    )

    page = forms.IntegerField(
        label=_("Page"),
        widget=forms.HiddenInput(),
        required=False,
        initial=1,
    )

    class Media:
        js = [
            # DependsOn
            'js/dependsOn.min.js',
            # Mask
            'js/jquery.mask.min.js',
        ]

    def __init__(self, load_labels=False, *args, **kwargs):
        if kwargs.get('data'):
            kwargs['data'] = kwargs['data'].copy()
            kwargs['data'].setdefault('taille_page', DEFAULT_PAGINATOR_SIZE)

        super().__init__(*args, **kwargs)

        # Initialize the labels of the autocomplete fields
        if load_labels:
            student = self.data.get(self.add_prefix('matricule_etudiant'))
            if student:
                person = Person.objects.values('last_name', 'first_name').filter(global_id=student).first()
                if person:
                    self.fields['matricule_etudiant'].widget.choices = (
                        (student, '{}, {}'.format(person['last_name'], person['first_name'])),
                    )

    def clean_numero(self):
        numero = self.cleaned_data.get('numero')
        return re.search(REGEX_REFERENCE, numero).group(0).replace('.', '') if numero else ''

    def clean_taille_page(self):
        return self.cleaned_data.get('taille_page') or self.fields['taille_page'].initial

    def clean_page(self):
        return self.cleaned_data.get('page') or self.fields['page'].initial
