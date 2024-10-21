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
from typing import Optional

from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from django.test import TestCase
from django.utils.translation import gettext as _

from parcours_doctoral.ddd.domain.model.parcours_doctoral import ENTITY_CDE
from parcours_doctoral.forms.cdd.generic_send_mail import (
    BaseEmailTemplateForm,
    SelectCddEmailTemplateForm,
)
from parcours_doctoral.mail_templates import (
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_STUDENT,
)
from parcours_doctoral.tests.factories.mail_template import CddMailTemplateFactory
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory


class SelectCddEmailTemplateFormTestCase(TestCase):
    parcours_doctoral_with_custom_email_templates: Optional[ParcoursDoctoralFactory]
    parcours_doctoral_without_custom_email_template: Optional[ParcoursDoctoralFactory]
    first_doctoral_commission: Optional[EntityFactory]
    second_doctoral_commission: Optional[EntityFactory]
    identifier: str
    cdd_mail_template: Optional[CddMailTemplateFactory]

    @classmethod
    def setUpTestData(cls):
        cls.identifier = PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_STUDENT

        cls.first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=cls.first_doctoral_commission, acronym=ENTITY_CDE)

        cls.parcours_doctoral_with_custom_email_templates = ParcoursDoctoralFactory(
            training__management_entity=cls.first_doctoral_commission,
        )

        cls.cdd_mail_template = CddMailTemplateFactory(
            identifier=cls.identifier,
            language=cls.parcours_doctoral_with_custom_email_templates.student.language,
            cdd=cls.parcours_doctoral_with_custom_email_templates.training.management_entity,
            name="My custom mail",
        )

        cls.second_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=cls.second_doctoral_commission, acronym=ENTITY_CDE)

        cls.parcours_doctoral_without_custom_email_template = ParcoursDoctoralFactory(
            training__management_entity=cls.second_doctoral_commission,
        )

    def test_form_validation_with_no_data(self):
        form = SelectCddEmailTemplateForm(
            identifier=self.identifier,
            parcours_doctoral=self.parcours_doctoral_without_custom_email_template,
            data={},
        )

        self.assertFalse(form.is_valid())

        # Mandatory field
        self.assertIn('template', form.errors)

    def test_form_validation_with_no_custom_template(self):
        form = SelectCddEmailTemplateForm(
            identifier=self.identifier,
            parcours_doctoral=self.parcours_doctoral_without_custom_email_template,
            data={
                'template': self.identifier,
            },
        )

        self.assertTrue(form.is_valid())
        hidden_fields_names = [field.name for field in form.hidden_fields()]
        self.assertIn('template', hidden_fields_names)
        self.assertIn((self.identifier, _('Generic')), form.fields['template'].choices)

    def test_form_validation_with_custom_templates(self):
        form = SelectCddEmailTemplateForm(
            identifier=self.identifier,
            parcours_doctoral=self.parcours_doctoral_with_custom_email_templates,
            data={
                'template': self.identifier,
            },
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(len(form.hidden_fields()), 0)
        self.assertIn((self.identifier, _('Generic')), form.fields['template'].choices)
        self.assertIn((self.cdd_mail_template.pk, self.cdd_mail_template.name), form.fields['template'].choices)


class BaseEmailTemplateFormTestCase(TestCase):
    def test_form_validation_with_no_data(self):
        form = BaseEmailTemplateForm(
            data={},
        )

        self.assertFalse(form.is_valid())

        # Mandatory fields
        self.assertIn('subject', form.errors)
        self.assertIn('body', form.errors)

    def test_form_validation_with_valid_data(self):
        form = BaseEmailTemplateForm(
            data={
                'subject': 'The subject',
                'body': 'The content of the message',
            },
        )

        self.assertTrue(form.is_valid())
