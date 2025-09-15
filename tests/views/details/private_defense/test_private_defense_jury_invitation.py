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
from email.message import Message
from email.utils import getaddresses

from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from osis_history.models import HistoryEntry
from osis_notification.models import EmailNotification

from admission.tests.factories.doctorate import DoctorateFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ENTITY_CDE
from parcours_doctoral.mail_templates.private_defense import (
    PARCOURS_DOCTORAL_EMAIL_PRIVATE_DEFENSE_JURY_INVITATION,
)
from parcours_doctoral.tests.factories.jury import (
    ExternalJuryMemberFactory,
    JuryMemberFactory,
    JuryMemberWithExternalPromoterFactory,
    JuryMemberWithInternalPromoterFactory,
)
from parcours_doctoral.tests.factories.mail_template import CddMailTemplateFactory
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.private_defense import PrivateDefenseFactory
from parcours_doctoral.tests.mixins import MockOsisDocumentMixin


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class PrivateDefenseJuryInvitationViewTestCase(MockOsisDocumentMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=cls.doctoral_commission, acronym=ENTITY_CDE)

        cls.training = DoctorateFactory()

        cls.student = PersonFactory()
        cls.manager = ProgramManagerFactory(education_group=cls.training.education_group).person

        cls.namespace = 'parcours_doctoral:private-defense:jury-invitation'
        cls.details_namespace = 'parcours_doctoral:private-defense'

    def setUp(self):
        super().setUp()

        self.doctorate = ParcoursDoctoralFactory(
            training=self.training,
            student=self.student,
            status=ChoixStatutParcoursDoctoral.ADMIS.name,
        )

        self.jury_member = JuryMemberFactory(
            person__first_name='John',
            person__last_name='Poe',
            person__email='john.poe@test.be',
            person__language=settings.LANGUAGE_CODE_EN,
            parcours_doctoral=self.doctorate,
        )
        self.external_jury_member = ExternalJuryMemberFactory(
            first_name='Jim',
            last_name='Poe',
            email='jim.poe@test.be',
            parcours_doctoral=self.doctorate,
        )
        self.jury_member_with_internal_promoter = JuryMemberWithInternalPromoterFactory(
            promoter__actor_ptr__person__first_name='Jane',
            promoter__actor_ptr__person__last_name='Doe',
            promoter__actor_ptr__person__email='jane.doe@test.be',
            parcours_doctoral=self.doctorate,
        )
        self.jury_member_with_external_promoter = JuryMemberWithExternalPromoterFactory(
            promoter__first_name='Tom',
            promoter__last_name='Doe',
            promoter__language=settings.LANGUAGE_CODE_EN,
            promoter__email='tom.doe@test.be',
            parcours_doctoral=self.doctorate,
        )

        self.private_defense = PrivateDefenseFactory(parcours_doctoral=self.doctorate)

        self.url = resolve_url(self.namespace, uuid=self.doctorate.uuid)
        self.details_url = resolve_url(self.details_namespace, uuid=self.doctorate.uuid)

    def test_get_jury_invitation_form(self):
        self.client.force_login(self.manager.user)

        self.doctorate.status = ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_AUTORISEE.name
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

        self.assertTrue(form.fields['subject'].disabled)
        self.assertTrue(form.fields['body'].disabled)

    def test_jury_invitation(self):
        self.client.force_login(self.manager.user)

        fr_cdd_template = CddMailTemplateFactory(
            identifier=PARCOURS_DOCTORAL_EMAIL_PRIVATE_DEFENSE_JURY_INVITATION,
            language=settings.LANGUAGE_CODE_FR,
            cdd=self.doctorate.training.management_entity,
            name="My custom mail",
            subject='FR[{jury_member_first_name}-{jury_member_last_name}]',
            body='FR[]',
        )

        en_cdd_template = CddMailTemplateFactory(
            identifier=PARCOURS_DOCTORAL_EMAIL_PRIVATE_DEFENSE_JURY_INVITATION,
            language=settings.LANGUAGE_CODE_EN,
            cdd=self.doctorate.training.management_entity,
            name="My custom mail",
            subject='EN[{jury_member_first_name}-{jury_member_last_name}]',
            body='EN[]',
        )

        # Invalid status
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

        # Valid status
        self.doctorate.status = ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_AUTORISEE.name
        self.doctorate.save(update_fields=['status'])

        response = self.client.post(self.url)

        self.assertRedirects(response, expected_url=self.details_url)

        history_entries = HistoryEntry.objects.filter(object_uuid=self.doctorate.uuid)

        self.assertEqual(len(history_entries), 1)

        self.assertCountEqual(history_entries[0].tags, ['parcours_doctoral', 'private-defense'])

        # Check a custom (tokens and language) notification has been sent to each jury member
        notifications = EmailNotification.objects.all()

        self.assertEqual(len(notifications), 4)

        notification_by_email_address: dict[str, EmailNotification] = {}
        email_message_by_email_address: dict[str, Message] = {}

        for notification in notifications:
            email_message = message_from_string(notification.payload)
            to_email_address = [address for _, address in getaddresses(email_message.get_all('To', [('', '')]))]
            notification_by_email_address[to_email_address[0]] = notification
            email_message_by_email_address[to_email_address[0]] = email_message

        internal_promoter_email = self.jury_member_with_internal_promoter.promoter.person.email
        self.assertIn(internal_promoter_email, notification_by_email_address)
        self.assertEqual(
            notification_by_email_address[internal_promoter_email].person,
            self.jury_member_with_internal_promoter.promoter.person,
        )
        email_message = email_message_by_email_address[internal_promoter_email]
        self.assertEqual(email_message.get('subject'), 'FR[Jane-Doe]')

        external_promoter_email = self.jury_member_with_external_promoter.promoter.email
        self.assertIn(external_promoter_email, notification_by_email_address)
        self.assertEqual(notification_by_email_address[external_promoter_email].person, None)
        email_message = email_message_by_email_address[external_promoter_email]
        self.assertEqual(email_message.get('subject'), 'EN[Tom-Doe]')

        internal_jury_member_email = self.jury_member.person.email
        self.assertIn(internal_jury_member_email, notification_by_email_address)
        self.assertEqual(notification_by_email_address[internal_jury_member_email].person, self.jury_member.person)
        email_message = email_message_by_email_address[internal_jury_member_email]
        self.assertEqual(email_message.get('subject'), 'EN[John-Poe]')

        external_jury_member_email = self.external_jury_member.email
        self.assertIn(external_jury_member_email, notification_by_email_address)
        self.assertEqual(notification_by_email_address[external_jury_member_email].person, None)
        email_message = email_message_by_email_address[external_jury_member_email]
        self.assertEqual(email_message.get('subject'), 'FR[Jim-Poe]')
