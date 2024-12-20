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

from unittest.mock import patch

from base.tests.factories.person import PersonFactory
from base.tests.factories.user import SuperUserFactory, UserFactory
from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase
from osis_mail_template import templates
from rest_framework import status

from parcours_doctoral.mail_templates import (
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT,
)
from parcours_doctoral.models.cdd_mail_template import CddMailTemplate
from parcours_doctoral.tests.factories.roles import CddConfiguratorFactory


class CddMailTemplatesTestCase(TestCase):
    def setUp(self):
        self.lambda_user = UserFactory()
        manager = CddConfiguratorFactory()
        self.cdd = manager.entity
        self.cdd_user = manager.person.user

        self.list_url = resolve_url('parcours_doctoral:config:cdd-mail-template:list')

        self.cdd_mail_template = CddMailTemplate.objects.create(
            identifier=PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT,
            name="Some name",
            language=settings.LANGUAGE_CODE_EN,
            cdd=self.cdd,
            subject="Subject",
            body="Body",
        )
        CddMailTemplate(
            identifier=PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT,
            name="Some name",
            language=settings.LANGUAGE_CODE_FR,
            cdd=self.cdd,
            subject="Sujet",
            body="Corps",
        ).save()
        self.preview_url = resolve_url(
            'parcours_doctoral:config:cdd-mail-template:preview',
            identifier=PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT,
            pk=self.cdd_mail_template.pk,
        )
        self.add_url = resolve_url(
            'parcours_doctoral:config:cdd-mail-template:add',
            identifier=PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT,
        )
        self.edit_url = resolve_url(
            'parcours_doctoral:config:cdd-mail-template:edit',
            identifier=PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT,
            pk=self.cdd_mail_template.pk,
        )
        self.delete_url = resolve_url(
            'parcours_doctoral:config:cdd-mail-template:delete',
            identifier=PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT,
            pk=self.cdd_mail_template.pk,
        )

        self.data = {
            "name": "Nom",
            "cdd": self.cdd.id,
            "fr-be-subject": "Sujet",
            "fr-be-body": "Corps",
            "en-subject": "Subject",
            "en-body": "Body",
        }

    @patch('osis_mail_template.registry.MailTemplateRegistry.get_description', return_value="Foo")
    def test_str(self, *args):
        self.assertEqual(str(self.cdd_mail_template), "Some name (depuis Foo en Anglais)")

    def test_lambda_user_is_not_allowed(self):
        self.client.force_login(self.lambda_user)
        self.assertEqual(self.client.get(self.list_url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get(self.preview_url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get(self.edit_url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get(self.add_url).status_code, status.HTTP_403_FORBIDDEN)

    @patch(
        'parcours_doctoral.models.cdd_mail_template.ALLOWED_CUSTOM_IDENTIFIERS',
        [PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT],
    )
    def test_list_as_cdd(self):
        self.client.force_login(self.cdd_user)

        response = self.client.get(self.list_url)
        self.assertContains(response, "Some name", status_code=status.HTTP_200_OK)
        self.assertContains(
            response, templates.get_description(PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT)
        )

    def test_list_as_superuser(self):
        superuser = SuperUserFactory()
        self.client.force_login(superuser)
        PersonFactory(user=superuser)

        response = self.client.get(self.list_url)
        self.assertContains(response, "Current user has no CDD", status_code=status.HTTP_403_FORBIDDEN)

    def test_preview_as_cdd(self):
        self.client.force_login(self.cdd_user)

        response = self.client.get(self.preview_url)
        self.assertContains(response, "Some name", status_code=status.HTTP_200_OK)

    def test_preview_error_as_cdd(self):
        # Someone has injected a wrong token (the template may have changed)
        self.cdd_mail_template.subject = "Subject {wrong_token}"
        self.cdd_mail_template.save()
        self.client.force_login(self.cdd_user)

        response = self.client.get(self.preview_url)
        self.assertContains(response, "TOKEN_wrong_token_UNDEFINED", status_code=status.HTTP_200_OK)

        self.cdd_mail_template.subject = "Subject"
        self.cdd_mail_template.save()

    def test_edit_as_cdd(self):
        self.client.force_login(self.cdd_user)

        response = self.client.get(self.edit_url)
        self.assertContains(response, "Some name", status_code=status.HTTP_200_OK)

        # Some error in tokens
        response = self.client.post(
            self.edit_url,
            {**self.data, 'name': "Nom modifié", "en-subject": "Subject {wrong_token}"},
        )
        self.assertContains(response, "wrong_token", status_code=status.HTTP_200_OK)

        response = self.client.post(
            self.edit_url,
            {**self.data, 'name': "Nom modifié", "fr-be-subject": "Sujet modifié"},
        )
        self.assertRedirects(response, self.list_url)
        self.assertEqual(CddMailTemplate.objects.filter(name="Nom modifié").count(), 2)

        # Save and preview
        response = self.client.post(
            self.edit_url,
            {**self.data, 'name': "Nom re-modifié", '_preview': 1},
        )
        self.assertRedirects(response, self.preview_url)
        self.assertEqual(CddMailTemplate.objects.filter(name="Nom re-modifié").count(), 2)

    @patch('osis_mail_template.registry.MailTemplateRegistry.get_description', return_value="Foo")
    def test_add_as_cdd(self, *args):
        self.client.force_login(self.cdd_user)

        response = self.client.get(self.add_url)
        self.assertContains(response, "Foo", status_code=status.HTTP_200_OK)

        response = self.client.post(self.add_url, {**self.data, 'name': "Nom ajouté"})
        self.assertRedirects(response, self.list_url)

    def test_add_as_superuser(self):
        superuser = SuperUserFactory()
        self.client.force_login(superuser)
        PersonFactory(user=superuser)

        response = self.client.get(self.add_url)
        self.assertContains(response, "Current user has no CDD", status_code=status.HTTP_403_FORBIDDEN)

    def test_delete_as_cdd(self):
        self.client.force_login(self.cdd_user)

        response = self.client.get(self.delete_url)
        self.assertContains(response, "Some name", status_code=status.HTTP_200_OK)
        response = self.client.post(self.delete_url)
        self.assertRedirects(response, self.list_url)
        self.assertEqual(CddMailTemplate.objects.filter(name="Nom modifié").count(), 0)
