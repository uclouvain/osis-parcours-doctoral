# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
import datetime

from django.test import TestCase
from django.utils.translation import gettext as _

from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.forms.confirmation import (
    ConfirmationForm,
    ConfirmationRetakingForm,
)


class ConfirmationTestCase(TestCase):
    def test_form_validation_with_no_data(self):
        form = ConfirmationForm(data={})

        self.assertFalse(form.is_valid())

        # Mandatory fields
        self.assertIn('date_limite', form.errors)
        self.assertIn('date', form.errors)

    def test_form_validation_with_no_data_when_admitted(self):
        form = ConfirmationForm(data={}, parcours_doctoral_status=ChoixStatutParcoursDoctoral.ADMIS.name)

        self.assertFalse(form.is_valid())

        # Mandatory fields
        self.assertIn('date_limite', form.errors)

    def test_form_validation_with_valid_dates(self):
        form = ConfirmationForm(
            data={
                'date_limite': datetime.date(2022, 1, 4),
                'date': datetime.date(2022, 1, 3),
            },
        )
        self.assertTrue(form.is_valid())


class ConfirmationRetakingFormTestCase(TestCase):
    def test_form_validation_with_no_data(self):
        form = ConfirmationRetakingForm(
            data={},
        )

        self.assertFalse(form.is_valid())

        # Mandatory fields
        self.assertIn('subject', form.errors)
        self.assertIn('body', form.errors)
        self.assertIn('date_limite', form.errors)

    def test_form_validation_with_valid_data(self):
        form = ConfirmationRetakingForm(
            data={
                'subject': 'The subject',
                'body': 'The content of the message',
                'date_limite': datetime.date(2022, 5, 1),
            },
        )

        self.assertTrue(form.is_valid())
