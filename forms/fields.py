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
from typing import List, Mapping, Optional, Union, Iterable

from django import forms
from django.utils.translation import gettext_lazy as _


class SelectOrOtherWidget(forms.MultiWidget):
    """Form widget to handle a configurable (from CDDConfiguration) list of choices, or other"""

    template_name = 'parcours_doctoral/forms/select_or_other_widget.html'
    media = forms.Media(
        js=[
            'js/dependsOn.min.js',
            'parcours_doctoral/js/select_or_other.js',
        ]
    )

    def __init__(self, *args, **kwargs):
        widgets = {
            '': forms.Select(),
            'other': forms.TextInput(),
        }
        super().__init__(widgets, *args, **kwargs)

    def decompress(self, value):
        # No value, no value to both fields
        if not value:
            return [None, None]
        # Pass value to radios if part of choices
        if value in dict(self.widgets[0].choices):
            return [value, '']
        # else pass value to textinput
        return ['other', value]

    def get_context(self, name: str, value, attrs):
        context = super().get_context(name, value, attrs)
        # Remove the required attribute on textinput
        context['widget']['subwidgets'][1]['attrs']['required'] = False
        return context


class SelectOrOtherField(forms.MultiValueField):
    """Form field to handle a list of choices, or other"""

    widget = SelectOrOtherWidget
    select_class = forms.ChoiceField

    def __init__(self, choices: Optional[Union[List[str], Mapping[str, str]]] = None, *args, **kwargs):
        select_kwargs = {}
        if choices is not None:
            choices = zip(choices, choices) if not isinstance(choices[0], (list, tuple)) else choices
            select_kwargs['choices'] = self.choices = list(choices) + [('other', _("Other"))]
        fields = [self.select_class(required=False, **select_kwargs), forms.CharField(required=False)]
        super().__init__(fields, require_all_fields=False, *args, **kwargs)

    def get_bound_field(self, form, field_name):
        if not self.widget.widgets[0].choices:
            self.widget.widgets[0].choices = self.choices
        return super().get_bound_field(form, field_name)

    def validate(self, value):
        # We do require all fields, but we want to check the final (compressed value)
        super(forms.MultiValueField, self).validate(value)

    def compress(self, data_list):
        # On save, take the other value if "other" is chosen
        if len(data_list) == 2:
            radio, other = data_list
            return radio if radio != "other" else other
        return ''

    def clean(self, value):
        # Dispatch the correct values to each field before regular cleaning
        radio, other = value
        if hasattr(self, 'choices') and radio not in self.choices and other is None:
            value = ['other', radio]
        return super().clean(value)

    def widget_attrs(self, widget):
        if self.help_text:
            return {'help_text': self.help_text}
        return super().widget_attrs(widget)


class SelectWithDisabledOptions(forms.Select):
    def __init__(
        self,
        enabled_options: Iterable[str] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.enabled_options = enabled_options

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        created_option = super().create_option(name, value, label, selected, index, subindex, attrs)

        if value not in self.enabled_options:
            created_option['attrs']['disabled'] = 'disabled'

        return created_option
