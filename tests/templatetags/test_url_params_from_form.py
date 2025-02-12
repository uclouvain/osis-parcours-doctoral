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
from django.test import TestCase

from parcours_doctoral.templatetags.parcours_doctoral import url_params_from_form


class UrlParamsTestCase(TestCase):
    class MyForm(forms.Form):
        char_field = forms.CharField(required=False, max_length=5)
        multiple_choice_field = forms.MultipleChoiceField(required=False, choices=[['a', 'a'], ['b', 'b'], ['c', 'c']])

    def test_with_no_bound_form(self):
        form = self.MyForm()

        self.assertEqual('', url_params_from_form(form))

    def test_with_invalid_form(self):
        form = self.MyForm(data={'char_field': '123456'})

        self.assertEqual('', url_params_from_form(form))

    def test_field_valid_form_with_missing_values(self):
        form = self.MyForm(data={})

        self.assertEqual('', url_params_from_form(form))

    def test_with_valid_form(self):
        form = self.MyForm(data={'char_field': '123', 'multiple_choice_field': ['a', 'b']})

        self.assertEqual('&char_field=123&multiple_choice_field=a&multiple_choice_field=b', url_params_from_form(form))
