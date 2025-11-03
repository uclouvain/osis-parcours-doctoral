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
import datetime
from email import message_from_string
from email.utils import getaddresses
from uuid import uuid4

from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.translation import gettext
from osis_history.models import HistoryEntry
from osis_notification.models import EmailNotification

from admission.tests.factories.doctorate import DoctorateFactory
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ENTITY_CDE
from parcours_doctoral.mail_templates.public_defense import (
    PARCOURS_DOCTORAL_EMAIL_PUBLIC_DEFENSE_ON_SUCCESS,
)
from parcours_doctoral.tests.factories.mail_template import CddMailTemplateFactory
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.roles import ScebManagerRoleFactory
from parcours_doctoral.tests.mixins import MockOsisDocumentMixin


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class PublicDefenseSuccessViewTestCase(MockOsisDocumentMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=cls.doctoral_commission, acronym=ENTITY_CDE)

        cls.training = DoctorateFactory()

        cls.student = PersonFactory()
        cls.manager = ProgramManagerFactory(education_group=cls.training.education_group).person

        cls.sceb_manager = ScebManagerRoleFactory().person

        cls.namespace = 'parcours_doctoral:public-defense:success'
        cls.details_namespace = 'parcours_doctoral:public-defense'

        cls.data = {
            'success-subject': 'Subject',
            'success-body': 'Body',
        }

    def setUp(self):
        super().setUp()

        self.doctorate = ParcoursDoctoralFactory(
            training=self.training,
            student=self.student,
            status=ChoixStatutParcoursDoctoral.SOUTENANCE_PUBLIQUE_AUTORISEE.name,
            defense_minutes=[uuid4()],
            defense_datetime=datetime.datetime(2025, 2, 1, 11, 30),
        )

        self.url = resolve_url(self.namespace, uuid=self.doctorate.uuid)
        self.details_url = resolve_url(self.details_namespace, uuid=self.doctorate.uuid)

    def test_get_success_form(self):
        self.client.force_login(self.manager.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertTrue(form.initial.get('subject'))
        self.assertTrue(form.initial.get('body'))

        self.assertNotIn('TOKEN_', form.initial['subject'])
        self.assertNotIn('_UNDEFINED', form.initial['subject'])
        self.assertNotIn('TOKEN_', form.initial['body'])
        self.assertNotIn('_UNDEFINED', form.initial['body'])

        # With cdd email templates
        fr_cdd_template = CddMailTemplateFactory(
            identifier=PARCOURS_DOCTORAL_EMAIL_PUBLIC_DEFENSE_ON_SUCCESS,
            language=settings.LANGUAGE_CODE_FR,
            cdd=self.doctorate.training.management_entity,
            name="My custom mail",
            subject='FR[SUBJECT]',
            body='FR[BODY]',
        )

        en_cdd_template = CddMailTemplateFactory(
            identifier=PARCOURS_DOCTORAL_EMAIL_PUBLIC_DEFENSE_ON_SUCCESS,
            language=settings.LANGUAGE_CODE_EN,
            cdd=self.doctorate.training.management_entity,
            name="My custom mail",
            subject='EN[SUBJECT]',
            body='EN[BODY]',
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(form.initial.get('subject'), 'FR[SUBJECT]')
        self.assertEqual(form.initial.get('body'), 'FR[BODY]')

    def test_with_invalid_doctorate_status(self):
        self.client.force_login(self.manager.user)

        self.doctorate.status = ChoixStatutParcoursDoctoral.SOUTENANCE_PUBLIQUE_SOUMISE.name
        self.doctorate.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_post_with_invalid_incomplete_email(self):
        self.client.force_login(self.manager.user)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('subject', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('body', []))

    def test_post_with_incomplete_doctorate(self):
        self.client.force_login(self.manager.user)

        self.doctorate.defense_datetime = None
        self.doctorate.save()

        response = self.client.post(self.url, data=self.data)

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn(
            gettext(
                'Please be sure that the date and time of the defence have been filled in and that the defence minutes '
                'have been submitted in the application.'
            ),
            form.errors.get('__all__', []),
        )

        self.doctorate.defense_datetime = datetime.datetime(2025, 1, 1, 11, 0)
        self.doctorate.defense_minutes = []
        self.doctorate.save()

        response = self.client.post(self.url, data=self.data)

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn(
            gettext(
                'Please be sure that the date and time of the defence have been filled in and that the defence minutes '
                'have been submitted in the application.'
            ),
            form.errors.get('__all__', []),
        )

    def test_post_valid_data(self):
        self.client.force_login(self.manager.user)

        response = self.client.post(self.url, data=self.data)

        self.assertRedirects(response, expected_url=self.details_url)

        self.doctorate.refresh_from_db()
        self.assertEqual(self.doctorate.status, ChoixStatutParcoursDoctoral.PROCLAME.name)

        history_entries = HistoryEntry.objects.filter(object_uuid=self.doctorate.uuid)

        self.assertEqual(len(history_entries), 1)

        self.assertCountEqual(history_entries[0].tags, ['parcours_doctoral', 'public-defense', 'status-changed'])

        notifications = EmailNotification.objects.filter(person=self.student)

        self.assertEqual(len(notifications), 1)
        email_message = message_from_string(notifications[0].payload)

        to_email_address = [address for _, address in getaddresses(email_message.get_all('To', [('', '')]))]
        cc_email_addresses = [address for _, address in getaddresses(email_message.get_all('Cc', []))]

        self.assertEqual(len(to_email_address), 1)
        self.assertEqual(to_email_address[0], self.student.email)

        self.assertEqual(len(cc_email_addresses), 1)
        self.assertEqual(cc_email_addresses[0], self.sceb_manager.email)
