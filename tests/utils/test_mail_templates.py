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
from django.conf import settings
from django.test import TestCase
from osis_mail_template.models import MailTemplate

from base.tests.factories.education_group_year import EducationGroupYearFactory
from parcours_doctoral.mail_templates.private_defense import (
    PARCOURS_DOCTORAL_EMAIL_PRIVATE_DEFENSE_AUTHORISATION,
    PARCOURS_DOCTORAL_EMAIL_PRIVATE_DEFENSE_JURY_INVITATION,
)
from parcours_doctoral.tests.factories.mail_template import CddMailTemplateFactory
from parcours_doctoral.utils.mail_templates import (
    get_email_template,
    get_email_templates_by_language,
)


class MailTemplatesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.first_training = EducationGroupYearFactory()
        cls.second_training = EducationGroupYearFactory()
        cls.generic_identifier = PARCOURS_DOCTORAL_EMAIL_PRIVATE_DEFENSE_AUTHORISATION
        cls.custom_identifier = PARCOURS_DOCTORAL_EMAIL_PRIVATE_DEFENSE_JURY_INVITATION

    def test_get_email_templates_by_language_with_no_template(self):
        templates = get_email_templates_by_language(
            identifier='UNKNOWN_TEMPLATE',
            management_entity_id=self.first_training.management_entity_id,
        )
        self.assertEqual(templates, {})

    def test_get_email_templates_by_language_with_generic_template(self):
        generic_templates = {
            mail_template.language: mail_template
            for mail_template in MailTemplate.objects.filter(identifier=self.generic_identifier)
        }

        templates = get_email_templates_by_language(
            identifier=self.generic_identifier,
            management_entity_id=self.first_training.management_entity_id,
        )

        self.assertEqual(len(templates), 2)

        self.assertEqual(
            templates.get(settings.LANGUAGE_CODE_FR),
            generic_templates.get(settings.LANGUAGE_CODE_FR),
        )

        self.assertEqual(
            templates.get(settings.LANGUAGE_CODE_EN),
            generic_templates.get(settings.LANGUAGE_CODE_EN),
        )

    def test_get_email_templates_by_language_with_custom_template(self):
        generic_templates = {
            mail_template.language: mail_template
            for mail_template in MailTemplate.objects.filter(identifier=self.custom_identifier)
        }

        fr_custom_template = CddMailTemplateFactory(
            identifier=self.custom_identifier,
            language=settings.LANGUAGE_CODE_FR,
            cdd=self.first_training.management_entity,
            name="My custom mail",
        )

        en_custom_template = CddMailTemplateFactory(
            identifier=self.custom_identifier,
            language=settings.LANGUAGE_CODE_EN,
            cdd=self.first_training.management_entity,
            name="My custom mail",
        )

        templates = get_email_templates_by_language(
            identifier=self.custom_identifier,
            management_entity_id=self.first_training.management_entity_id,
        )

        self.assertEqual(len(templates), 2)

        self.assertEqual(templates.get(settings.LANGUAGE_CODE_FR), fr_custom_template)
        self.assertEqual(templates.get(settings.LANGUAGE_CODE_EN), en_custom_template)

        # Other management entity -> use the generic templates
        templates = get_email_templates_by_language(
            identifier=self.custom_identifier,
            management_entity_id=self.second_training.management_entity_id,
        )

        self.assertEqual(len(templates), 2)

        self.assertEqual(
            templates.get(settings.LANGUAGE_CODE_FR),
            generic_templates.get(settings.LANGUAGE_CODE_FR),
        )

        self.assertEqual(
            templates.get(settings.LANGUAGE_CODE_EN),
            generic_templates.get(settings.LANGUAGE_CODE_EN),
        )

    def test_get_email_template_with_no_template(self):
        template = get_email_template(
            identifier='UNKNOWN_TEMPLATE',
            management_entity_id=self.first_training.management_entity_id,
            language=settings.LANGUAGE_CODE_FR,
        )
        self.assertIsNone(template)

    def test_get_email_template_with_generic_template(self):
        generic_templates = {
            mail_template.language: mail_template
            for mail_template in MailTemplate.objects.filter(identifier=self.generic_identifier)
        }

        template = get_email_template(
            identifier=self.generic_identifier,
            management_entity_id=self.first_training.management_entity_id,
            language=settings.LANGUAGE_CODE_FR,
        )

        self.assertEqual(template, generic_templates.get(settings.LANGUAGE_CODE_FR))

        template = get_email_template(
            identifier=self.generic_identifier,
            management_entity_id=self.first_training.management_entity_id,
            language=settings.LANGUAGE_CODE_EN,
        )

        self.assertEqual(template, generic_templates.get(settings.LANGUAGE_CODE_EN))

    def test_get_email_template_with_custom_template(self):
        generic_templates = {
            mail_template.language: mail_template
            for mail_template in MailTemplate.objects.filter(identifier=self.custom_identifier)
        }

        fr_custom_template = CddMailTemplateFactory(
            identifier=self.custom_identifier,
            language=settings.LANGUAGE_CODE_FR,
            cdd=self.first_training.management_entity,
            name="My custom mail",
        )

        en_custom_template = CddMailTemplateFactory(
            identifier=self.custom_identifier,
            language=settings.LANGUAGE_CODE_EN,
            cdd=self.first_training.management_entity,
            name="My custom mail",
        )

        template = get_email_template(
            identifier=self.custom_identifier,
            management_entity_id=self.first_training.management_entity_id,
            language=settings.LANGUAGE_CODE_FR,
        )

        self.assertEqual(template, fr_custom_template)

        template = get_email_template(
            identifier=self.custom_identifier,
            management_entity_id=self.first_training.management_entity_id,
            language=settings.LANGUAGE_CODE_EN,
        )

        self.assertEqual(template, en_custom_template)

        # Other management entity -> use the generic template
        template = get_email_template(
            identifier=self.custom_identifier,
            management_entity_id=self.second_training.management_entity_id,
            language=settings.LANGUAGE_CODE_FR,
        )

        self.assertEqual(template, generic_templates.get(settings.LANGUAGE_CODE_FR))
