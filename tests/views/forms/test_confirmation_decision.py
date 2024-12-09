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

import datetime
import uuid
from email import message_from_string
from typing import List, Optional
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from osis_async.models.enums import TaskState
from osis_notification.models import EmailNotification
from rest_framework import status

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.epreuve_confirmation.commands import (
    RecupererEpreuvesConfirmationQuery,
)
from parcours_doctoral.exports.confirmation_success_attestation import (
    confirmation_success_attestation,
)
from parcours_doctoral.infrastructure.mixins.notification import NotificationMixin
from parcours_doctoral.mail_templates import (
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_STUDENT,
)
from parcours_doctoral.models.confirmation_paper import ConfirmationPaper
from parcours_doctoral.models.parcours_doctoral import ParcoursDoctoral
from parcours_doctoral.models.task import ParcoursDoctoralTask
from parcours_doctoral.tests.factories.confirmation_paper import (
    ConfirmationPaperFactory,
)
from parcours_doctoral.tests.factories.mail_template import CddMailTemplateFactory
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class DoctorateConfirmationDecisionViewTestCase(TestCase):
    parcours_doctoral_with_confirmation_papers = Optional[ParcoursDoctoralFactory]
    parcours_doctoral_without_confirmation_paper = Optional[ParcoursDoctoralFactory]
    confirmation_papers = List[ConfirmationPaperFactory]

    @classmethod
    def setUpTestData(cls):
        cls.confirm_remote_upload_patcher = patch('osis_document.api.utils.confirm_remote_upload')
        patched = cls.confirm_remote_upload_patcher.start()
        patched.return_value = '4bdffb42-552d-415d-9e4c-725f10dce228'

        cls.confirm_multiple_upload_patcher = patch('osis_document.contrib.fields.FileField._confirm_multiple_upload')
        patched = cls.confirm_multiple_upload_patcher.start()
        patched.side_effect = lambda _, value, __: ['4bdffb42-552d-415d-9e4c-725f10dce228'] if value else []

        cls.get_remote_metadata_patcher = patch('osis_document.api.utils.get_remote_metadata')
        patched = cls.get_remote_metadata_patcher.start()
        patched.return_value = {"name": "test.pdf", "size": 1}

        cls.get_remote_token_patcher = patch('osis_document.api.utils.get_remote_token')
        patched = cls.get_remote_token_patcher.start()
        patched.return_value = 'foobar'

        cls.save_raw_content_remotely_patcher = patch('osis_document.utils.save_raw_content_remotely')
        patched = cls.save_raw_content_remotely_patcher.start()
        patched.return_value = 'a-token'

        cls.file_confirm_upload_patcher = patch('osis_document.contrib.fields.FileField._confirm_multiple_upload')
        patched = cls.file_confirm_upload_patcher.start()
        patched.side_effect = lambda _, value, __: ['4bdffb42-552d-415d-9e4c-725f10dce228'] if value else []

        cls.get_mandates_service_patcher = patch('reference.services.mandates.MandatesService.get')
        patched = cls.get_mandates_service_patcher.start()
        patched.return_value = [
            {
                'first_name': 'Jane',
                'last_name': 'Doe',
                'function': 'Présidente',
            }
        ]

        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        # Create parcours_doctorals
        cls.parcours_doctoral_without_confirmation_paper = ParcoursDoctoralFactory(
            training__academic_year=academic_years[0],
            status=ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name,
        )
        cls.parcours_doctoral_with_confirmation_papers = ParcoursDoctoralFactory(
            training=cls.parcours_doctoral_without_confirmation_paper.training,
            status=ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name,
        )
        cls.parcours_doctoral_with_incomplete_confirmation_paper = ParcoursDoctoralFactory(
            training=cls.parcours_doctoral_without_confirmation_paper.training,
            status=ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name,
        )
        cls.file_uuid = uuid.uuid4()
        cls.confirmation_papers = [
            ConfirmationPaperFactory(
                parcours_doctoral=cls.parcours_doctoral_with_confirmation_papers,
                confirmation_date=datetime.date(2022, 4, 1),
                confirmation_deadline=datetime.date(2022, 4, 5),
                supervisor_panel_report=[cls.file_uuid],
            ),
            ConfirmationPaperFactory(
                parcours_doctoral=cls.parcours_doctoral_with_incomplete_confirmation_paper,
                confirmation_deadline=datetime.date(2022, 4, 5),
                supervisor_panel_report=[cls.file_uuid],
                confirmation_date=None,
            ),
        ]

        cls.manager = ProgramManagerFactory(
            education_group=cls.parcours_doctoral_without_confirmation_paper.training.education_group
        ).person.user

        cls.custom_cdd_mail_template = CddMailTemplateFactory(
            identifier=PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_STUDENT,
            language=cls.parcours_doctoral_with_confirmation_papers.student.language,
            cdd=cls.parcours_doctoral_with_confirmation_papers.training.management_entity,
            name='My custom mail',
            subject='The email subject',
            body='The email body',
        )

        cls.success_path = 'parcours_doctoral:confirmation:success'
        cls.failure_path = 'parcours_doctoral:confirmation:failure'
        cls.retaking_path = 'parcours_doctoral:confirmation:retaking'

    def setUp(self):
        self.client.force_login(user=self.manager)
        cache.clear()

        # Mock weasyprint
        patcher = patch('parcours_doctoral.exports.utils.get_pdf_from_template', return_value=b'some content')
        patcher.start()
        self.addCleanup(patcher.stop)

    @classmethod
    def tearDownClass(cls):
        cls.confirm_remote_upload_patcher.stop()
        cls.confirm_multiple_upload_patcher.stop()
        cls.get_remote_metadata_patcher.stop()
        cls.get_remote_token_patcher.stop()
        cls.save_raw_content_remotely_patcher.stop()
        cls.get_mandates_service_patcher.stop()
        cls.file_confirm_upload_patcher.stop()
        super().tearDownClass()

    def test_confirmation_success_decision_without_confirmation_paper(self):
        url = reverse(self.success_path, args=[self.parcours_doctoral_without_confirmation_paper.uuid])

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_confirmation_success_decision_with_confirmation_paper(self):
        url = reverse(self.success_path, args=[self.parcours_doctoral_with_confirmation_papers.uuid])

        response = self.client.post(url)
        self.assertRedirects(
            response,
            reverse(
                'parcours_doctoral:confirmation',
                args=[self.parcours_doctoral_with_confirmation_papers.uuid],
            ),
        )

        parcours_doctoral: ParcoursDoctoral = ParcoursDoctoral.objects.get(
            uuid=self.parcours_doctoral_with_confirmation_papers.uuid
        )
        self.assertEqual(parcours_doctoral.status, ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE.name)

        parcours_doctoral_task: ParcoursDoctoralTask = ParcoursDoctoralTask.objects.filter(
            parcours_doctoral=parcours_doctoral
        ).first()
        self.assertEqual(
            parcours_doctoral_task.type, ParcoursDoctoralTask.TaskType.CONFIRMATION_SUCCESS_ATTESTATION.name
        )
        self.assertEqual(parcours_doctoral_task.task.state, TaskState.PENDING.name)

        # Simulate the triggering of the async tasks
        confirmation_success_attestation(task_uuid=parcours_doctoral_task.task.uuid)
        # call_command("process_parcours_doctoral_tasks")
        parcours_doctoral_task.refresh_from_db()

        c = ConfirmationPaper.objects.filter(parcours_doctoral=parcours_doctoral).first()
        self.assertEqual(c.certificate_of_achievement, [uuid.UUID('4bdffb42-552d-415d-9e4c-725f10dce228')])

        # Check the notifications
        email_notifications = EmailNotification.objects.all()

        self.assertEqual(len(email_notifications), 3)
        email_messages = [message_from_string(notification.payload) for notification in email_notifications]

        self.assertCountEqual(
            [email_message['To'] for email_message in email_messages],
            [
                self.parcours_doctoral_with_confirmation_papers.student.email,
                NotificationMixin.ADRE_EMAIL,
                NotificationMixin.ADRI_EMAIL,
            ],
        )

    def test_confirmation_success_decision_with_incomplete_confirmation_paper(self):
        url = reverse(self.success_path, args=[self.parcours_doctoral_with_incomplete_confirmation_paper.uuid])

        response = self.client.post(url)
        self.assertRedirects(
            response,
            reverse(
                'parcours_doctoral:confirmation',
                args=[self.parcours_doctoral_with_incomplete_confirmation_paper.uuid],
            ),
        )

        parcours_doctoral: ParcoursDoctoral = ParcoursDoctoral.objects.get(
            uuid=self.parcours_doctoral_with_incomplete_confirmation_paper.uuid
        )
        self.assertEqual(parcours_doctoral.status, ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name)

    def test_get_confirmation_failure_decision_without_confirmation_paper(self):
        url = reverse(self.failure_path, args=[self.parcours_doctoral_without_confirmation_paper.uuid])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_confirmation_failure_decision_with_confirmation_paper_and_generic_email(self):
        url = reverse(self.failure_path, args=[self.parcours_doctoral_with_confirmation_papers.uuid])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.context.get('select_template_form'))
        message_form = response.context.get('form')
        self.assertIsNotNone(message_form)

    def test_get_confirmation_failure_decision_with_confirmation_paper_and_custom_email(self):
        url = reverse(self.failure_path, args=[self.parcours_doctoral_with_confirmation_papers.uuid])

        response = self.client.get(url, {'template': self.custom_cdd_mail_template.pk})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.context.get('select_template_form'))
        message_form = response.context.get('form')
        self.assertIsNotNone(message_form)
        self.assertEqual(message_form.initial.get('subject'), self.custom_cdd_mail_template.subject)
        self.assertEqual(message_form.initial.get('body'), self.custom_cdd_mail_template.body)

    def test_get_confirmation_failure_decision_with_confirmation_paper_and_custom_email_and_htmx(self):
        url = reverse(self.failure_path, args=[self.parcours_doctoral_with_confirmation_papers.uuid])

        response = self.client.get(
            url,
            {'template': self.custom_cdd_mail_template.pk},
            **{"HTTP_HX-Request": 'true'},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        message_form = response.context.get('form')
        self.assertIsNotNone(message_form)
        self.assertEqual(message_form.initial.get('subject'), self.custom_cdd_mail_template.subject)
        self.assertEqual(message_form.initial.get('body'), self.custom_cdd_mail_template.body)

    def test_post_confirmation_failure_decision_without_confirmation_paper(self):
        url = reverse(self.failure_path, args=[self.parcours_doctoral_without_confirmation_paper.uuid])

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_post_confirmation_failure_decision_with_confirmation_paper(self):
        url = reverse(self.failure_path, args=[self.parcours_doctoral_with_confirmation_papers.uuid])

        data = {
            'subject': 'The subject of the message',
            'body': 'The body of the message',
        }
        response = self.client.post(url, data)
        self.assertRedirects(
            response,
            reverse(
                'parcours_doctoral:confirmation',
                args=[self.parcours_doctoral_with_confirmation_papers.uuid],
            ),
        )

        parcours_doctoral: ParcoursDoctoral = ParcoursDoctoral.objects.get(
            uuid=self.parcours_doctoral_with_confirmation_papers.uuid
        )
        self.assertEqual(parcours_doctoral.status, ChoixStatutParcoursDoctoral.NON_AUTORISE_A_POURSUIVRE.name)

        # Check the notifications
        email_notifications = EmailNotification.objects.all()

        self.assertEqual(len(email_notifications), 3)
        email_messages = [message_from_string(notification.payload) for notification in email_notifications]

        self.assertCountEqual(
            [email_message['To'] for email_message in email_messages],
            [
                self.parcours_doctoral_with_confirmation_papers.student.email,
                NotificationMixin.ADRE_EMAIL,
                NotificationMixin.ADRI_EMAIL,
            ],
        )

    def test_post_confirmation_failure_decision_with_incomplete_confirmation_paper(self):
        url = reverse(self.failure_path, args=[self.parcours_doctoral_with_incomplete_confirmation_paper.uuid])

        data = {
            'subject': 'The subject of the message',
            'body': 'The body of the message',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(
            response,
            'form',
            None,
            [
                "L'épreuve de confirmation n'est pas complète : veuillez vous assurer que la date "
                "et le procès verbal de l'épreuve ont bien été complétés."
            ],
        )

        parcours_doctoral: ParcoursDoctoral = ParcoursDoctoral.objects.get(
            uuid=self.parcours_doctoral_with_incomplete_confirmation_paper.uuid
        )
        self.assertEqual(parcours_doctoral.status, ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name)

    def test_post_confirmation_failure_decision_with_incomplete_form(self):
        url = reverse(self.failure_path, args=[self.parcours_doctoral_with_confirmation_papers.uuid])

        response = self.client.post(url, {'subject': 'The subject of the message'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, 'form', 'body', ['Ce champ est obligatoire.'])

    def test_get_confirmation_retaking_decision_without_confirmation_paper(self):
        url = reverse(self.retaking_path, args=[self.parcours_doctoral_without_confirmation_paper.uuid])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_confirmation_retaking_decision_with_confirmation_paper_and_generic_email(self):
        url = reverse(self.retaking_path, args=[self.parcours_doctoral_with_confirmation_papers.uuid])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.context.get('select_template_form'))
        message_form = response.context.get('form')
        self.assertIsNotNone(message_form)

    def test_get_confirmation_retaking_decision_with_confirmation_paper_and_custom_email(self):
        url = reverse(self.retaking_path, args=[self.parcours_doctoral_with_confirmation_papers.uuid])

        response = self.client.get(url, {'template': self.custom_cdd_mail_template.pk})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.context.get('select_template_form'))
        message_form = response.context.get('form')
        self.assertIsNotNone(message_form)
        self.assertEqual(message_form.initial.get('subject'), self.custom_cdd_mail_template.subject)
        self.assertEqual(message_form.initial.get('body'), self.custom_cdd_mail_template.body)

    def test_get_confirmation_retaking_decision_with_confirmation_paper_and_custom_email_and_htmx(self):
        url = reverse(self.retaking_path, args=[self.parcours_doctoral_with_confirmation_papers.uuid])

        response = self.client.get(
            url,
            {'template': self.custom_cdd_mail_template.pk},
            **{"HTTP_HX-Request": 'true'},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        message_form = response.context.get('form')
        self.assertIsNotNone(message_form)
        self.assertEqual(message_form.initial.get('subject'), self.custom_cdd_mail_template.subject)
        self.assertEqual(message_form.initial.get('body'), self.custom_cdd_mail_template.body)

    def test_post_confirmation_retaking_decision_without_confirmation_paper(self):
        url = reverse(self.retaking_path, args=[self.parcours_doctoral_without_confirmation_paper.uuid])

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_post_confirmation_retaking_decision_with_confirmation_paper(self):
        url = reverse(self.retaking_path, args=[self.parcours_doctoral_with_confirmation_papers.uuid])

        data = {
            'subject': 'The subject of the message',
            'body': 'The body of the message',
            'date_limite': datetime.date(2022, 1, 1),
        }
        response = self.client.post(url, data)

        self.assertRedirects(
            response,
            reverse(
                'parcours_doctoral:confirmation',
                args=[self.parcours_doctoral_with_confirmation_papers.uuid],
            ),
        )

        parcours_doctoral: ParcoursDoctoral = ParcoursDoctoral.objects.get(
            uuid=self.parcours_doctoral_with_confirmation_papers.uuid
        )
        self.assertEqual(parcours_doctoral.status, ChoixStatutParcoursDoctoral.CONFIRMATION_A_REPRESENTER.name)

        # Check the notifications
        email_notifications = EmailNotification.objects.all()

        self.assertEqual(len(email_notifications), 3)
        email_messages = [message_from_string(notification.payload) for notification in email_notifications]

        self.assertCountEqual(
            [email_message['To'] for email_message in email_messages],
            [
                self.parcours_doctoral_with_confirmation_papers.student.email,
                NotificationMixin.ADRE_EMAIL,
                NotificationMixin.ADRI_EMAIL,
            ],
        )

        confirmation_papers = message_bus_instance.invoke(
            RecupererEpreuvesConfirmationQuery(parcours_doctoral_uuid=parcours_doctoral.uuid)
        )
        self.assertEqual(len(confirmation_papers), 2)
        self.assertEqual(confirmation_papers[0].date_limite, datetime.date(2022, 1, 1))

    def test_post_confirmation_retaking_decision_with_incomplete_confirmation_paper(self):
        url = reverse(self.retaking_path, args=[self.parcours_doctoral_with_incomplete_confirmation_paper.uuid])

        data = {
            'subject': 'The subject of the message',
            'body': 'The body of the message',
            'date_limite': datetime.date(2022, 1, 1),
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(
            response,
            'form',
            None,
            [
                "L'épreuve de confirmation n'est pas complète : veuillez vous assurer que la date "
                "et le procès verbal de l'épreuve ont bien été complétés."
            ],
        )

        parcours_doctoral: ParcoursDoctoral = ParcoursDoctoral.objects.get(
            uuid=self.parcours_doctoral_with_incomplete_confirmation_paper.uuid
        )
        self.assertEqual(parcours_doctoral.status, ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name)

        confirmation_papers = message_bus_instance.invoke(
            RecupererEpreuvesConfirmationQuery(parcours_doctoral_uuid=parcours_doctoral.uuid)
        )
        self.assertEqual(len(confirmation_papers), 1)

    def test_post_confirmation_retaking_decision_with_incomplete_form(self):
        url = reverse(self.retaking_path, args=[self.parcours_doctoral_with_confirmation_papers.uuid])

        data = {
            'subject': 'The subject of the message',
            'body': 'The body of the message',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, 'form', 'date_limite', ['Ce champ est obligatoire.'])
