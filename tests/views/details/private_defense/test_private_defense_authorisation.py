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
from email import message_from_string
from email.utils import getaddresses

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
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
from parcours_doctoral.models import ActorType, ParcoursDoctoralSupervisionActor
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.private_defense import PrivateDefenseFactory
from parcours_doctoral.tests.mixins import MockOsisDocumentMixin


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class PrivateDefenseAuthorisationViewTestCase(MockOsisDocumentMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=cls.doctoral_commission, acronym=ENTITY_CDE)

        cls.training = DoctorateFactory()

        cls.student = PersonFactory()
        cls.manager = ProgramManagerFactory(education_group=cls.training.education_group).person

        cls.namespace = 'parcours_doctoral:private-defense:authorise'
        cls.details_namespace = 'parcours_doctoral:private-defense'

    def setUp(self):
        super().setUp()

        self.doctorate = ParcoursDoctoralFactory(
            training=self.training,
            student=self.student,
            status=ChoixStatutParcoursDoctoral.ADMIS.name,
        )

        self.private_defense = PrivateDefenseFactory(parcours_doctoral=self.doctorate)

        self.url = resolve_url(self.namespace, uuid=self.doctorate.uuid)
        self.details_url = resolve_url(self.details_namespace, uuid=self.doctorate.uuid)

    def test_get_authorisation_form(self):
        self.client.force_login(self.manager.user)

        self.doctorate.status = ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE.name
        self.doctorate.save(update_fields=['status'])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertTrue(form.initial.get('subject'))
        self.assertTrue(form.initial.get('body'))

        self.assertNotIn('TOKEN_', form.initial['subject'])
        self.assertNotIn('_UNDEFINED', form.initial['subject'])
        self.assertNotIn('TOKEN_', form.initial['body'])
        self.assertNotIn('_UNDEFINED', form.initial['body'])

    def test_authorisation(self):
        self.client.force_login(self.manager.user)

        # Invalid status
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

        # Valid status but no submitted data
        self.doctorate.status = ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE.name
        self.doctorate.save(update_fields=['status'])

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)

        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('subject', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('body', []))

        # Valid status and data
        response = self.client.post(self.url, data={'authorise-subject': 'Subject', 'authorise-body': 'Body'})

        self.assertRedirects(response, expected_url=self.details_url)

        self.doctorate.refresh_from_db()
        self.assertEqual(self.doctorate.status, ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_AUTORISEE.name)

        history_entries = HistoryEntry.objects.filter(object_uuid=self.doctorate.uuid)

        self.assertEqual(len(history_entries), 1)

        self.assertCountEqual(history_entries[0].tags, ['parcours_doctoral', 'private-defense', 'status-changed'])

        notifications = EmailNotification.objects.filter(person=self.student)

        self.assertEqual(len(notifications), 1)
        email_message = message_from_string(notifications[0].payload)

        to_email_address = [address for _, address in getaddresses(email_message.get_all('To', [('', '')]))]
        cc_email_addresses = [address for _, address in getaddresses(email_message.get_all('Cc', []))]

        promoters_emails = [
            promoter.email
            for promoter in ParcoursDoctoralSupervisionActor.objects.filter(
                type=ActorType.PROMOTER.name,
                process_id=self.doctorate.supervision_group_id,
            )
        ]

        self.assertEqual(to_email_address[0], self.student.email)
        self.assertCountEqual(cc_email_addresses, promoters_emails)
