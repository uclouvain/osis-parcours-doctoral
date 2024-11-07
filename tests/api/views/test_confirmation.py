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
from unittest.mock import patch
from uuid import UUID

from django.shortcuts import resolve_url
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from parcours_doctoral.models.confirmation_paper import ConfirmationPaper
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.epreuve_confirmation.validators.exceptions import (
    EpreuveConfirmationDateIncorrecteException,
    EpreuveConfirmationNonTrouveeException,
)
from parcours_doctoral.tests.factories import WriteTokenFactory
from parcours_doctoral.tests.factories.supervision import PromoterFactory
from base.models.enums.entity_type import EntityType
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from osis_notification.models import WebNotification

from parcours_doctoral.tests.factories.confirmation_paper import ConfirmationPaperFactory
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class ConfirmationAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Create supervision group members
        promoter = PromoterFactory()
        other_promoter = PromoterFactory()

        # Create parcours_doctoral management entity
        root = EntityVersionFactory(parent=None).entity
        sector = EntityVersionFactory(
            parent=root,
            entity_type=EntityType.SECTOR.name,
            acronym='SST',
        ).entity
        commission = EntityVersionFactory(
            parent=sector,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        ).entity
        cls.parcours_doctoral = ParcoursDoctoralFactory(
            status=ChoixStatutParcoursDoctoral.ADMITTED.name,
            training__management_entity=commission,
            supervision_group=promoter.process,
        )
        parcours_doctoral = ParcoursDoctoralFactory(
            training__management_entity=commission,
            student=cls.parcours_doctoral.student,
        )
        other_parcours_doctoral = ParcoursDoctoralFactory(
            status=ChoixStatutParcoursDoctoral.ADMITTED.name,
            training__management_entity=commission,
            supervision_group=other_promoter.process,
        )

        # Users
        cls.student = cls.parcours_doctoral.student
        cls.other_student = other_parcours_doctoral.student
        cls.promoter = promoter.person.user
        cls.other_promoter = other_promoter.person.user
        cls.manager = ProgramManagerFactory(education_group=cls.parcours_doctoral.training.education_group).person

        cls.parcours_doctoral_url = resolve_url('parcours_doctoral_api_v1:confirmation', uuid=cls.parcours_doctoral.uuid)
        cls.other_parcours_doctoral_url = resolve_url('parcours_doctoral_api_v1:confirmation', uuid=other_parcours_doctoral.uuid)
        cls.parcours_doctoral_url = resolve_url('parcours_doctoral_api_v1:confirmation', uuid=parcours_doctoral.uuid)

        cls.supervised_parcours_doctoral_url = resolve_url('parcours_doctoral_api_v1:supervised_confirmation', uuid=cls.parcours_doctoral.uuid)
        cls.supervised_other_parcours_doctoral_url = resolve_url(
            'parcours_doctoral_api_v1:supervised_confirmation',
            uuid=other_parcours_doctoral.uuid,
        )
        cls.supervised_parcours_doctoral_url = resolve_url('parcours_doctoral_api_v1:supervised_confirmation', uuid=parcours_doctoral.uuid)

    @patch("osis_document.contrib.fields.FileField._confirm_multiple_upload")
    def setUp(self, confirm_upload):
        confirm_upload.side_effect = lambda _, value, __: ["550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92"] if value else []
        self.confirmation_papers = [
            ConfirmationPaperFactory(
                parcours_doctoral=self.parcours_doctoral,
                confirmation_date=datetime.date(2022, 4, 1),
                confirmation_deadline=datetime.date(2022, 4, 5),
                research_report=[WriteTokenFactory().token],
                supervisor_panel_report=[WriteTokenFactory().token],
                supervisor_panel_report_canvas=[WriteTokenFactory().token],
                research_mandate_renewal_opinion=[WriteTokenFactory().token],
            ),
            ConfirmationPaperFactory(
                parcours_doctoral=self.parcours_doctoral,
                confirmation_deadline=datetime.date(2022, 4, 10),
                research_report=[WriteTokenFactory().token],
                supervisor_panel_report=[WriteTokenFactory().token],
                supervisor_panel_report_canvas=[WriteTokenFactory().token],
                research_mandate_renewal_opinion=[WriteTokenFactory().token],
            ),
        ]

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.student.user)
        methods_not_allowed = [
            'delete',
            'patch',
            'post',
            'put',
        ]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.parcours_doctoral_url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_confirmation_student(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.parcours_doctoral_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        json_response = response.json()

        self.assertEqual(len(json_response), 2)

        # Check the first confirmation paper
        self.assertEqual(json_response[0]['uuid'], str(self.confirmation_papers[1].uuid))
        self.assertEqual(json_response[0]['date_limite'], '2022-04-10')
        self.assertIsNone(json_response[0]['date'])
        self.assertIsNone(json_response[0]['demande_prolongation'])

        # Check the second confirmation paper
        self.assertEqual(json_response[1]['uuid'], str(self.confirmation_papers[0].uuid))
        self.assertEqual(json_response[1]['date'], '2022-04-01')
        self.assertEqual(json_response[1]['date_limite'], '2022-04-05')
        self.assertIsNone(json_response[1]['demande_prolongation'])

    def test_get_confirmation_promoter(self):
        self.client.force_authenticate(user=self.promoter)
        response = self.client.get(self.parcours_doctoral_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_confirmation_promoter_with_parcours_doctoral_invalid_status(self):
        self.client.force_authenticate(user=self.promoter)
        response = self.client.get(self.parcours_doctoral_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_confirmation_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter)
        response = self.client.get(self.parcours_doctoral_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_confirmation_student_with_parcours_doctoral_invalid_status(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.parcours_doctoral_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_confirmation_with_parcours_doctoral_other_student(self):
        self.client.force_authenticate(user=self.other_student.user)
        response = self.client.get(self.parcours_doctoral_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("osis_document.contrib.fields.FileField._confirm_multiple_upload")
    def test_put_confirmation_promoter(self, confirm_upload):
        confirmation_paper_uuid = self.confirmation_papers[1].uuid

        token = WriteTokenFactory()

        confirm_upload.side_effect = lambda _, value, __: [token.upload.uuid] if value else []

        self.client.force_authenticate(user=self.promoter)

        response = self.client.put(
            self.supervised_parcours_doctoral_url,
            format='json',
            data={
                'proces_verbal_ca': [token.token],
                'avis_renouvellement_mandat_recherche': [token.token],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        self.assertEqual(response.json()['uuid'], str(self.parcours_doctoral.uuid))

        # Check the first confirmation paper
        confirmation_paper = ConfirmationPaper.objects.get(uuid=confirmation_paper_uuid)

        self.assertEqual(confirmation_paper.uuid, confirmation_paper_uuid)
        self.assertEqual(confirmation_paper.supervisor_panel_report, [token.upload.uuid])
        self.assertEqual(confirmation_paper.research_mandate_renewal_opinion, [token.upload.uuid])

        # Check the notifications
        self.assertEqual(WebNotification.objects.count(), 1)
        notification = WebNotification.objects.first()
        self.assertEqual(notification.person, self.manager)

    def test_put_confirmation_by_promoter_with_invalid_parcours_doctoral_status(self):
        self.client.force_authenticate(user=self.promoter)
        response = self.client.put(
            self.supervised_parcours_doctoral_url,
            format='json',
            data={
                'proces_verbal_ca': ['f1'],
                'avis_renouvellement_mandat_recherche': ['f2'],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_confirmation_by_promoter_with_parcours_doctoral_other_student(self):
        self.client.force_authenticate(user=self.promoter)
        response = self.client.put(
            self.supervised_other_parcours_doctoral_url,
            format='json',
            data={
                'proces_verbal_ca': ['f1'],
                'avis_renouvellement_mandat_recherche': ['f2'],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_confirmation_by_promoter_with_parcours_doctoral_without_confirmation_paper(self):
        self.client.force_authenticate(user=self.other_promoter)
        response = self.client.put(
            self.supervised_other_parcours_doctoral_url,
            format='json',
            data={
                'proces_verbal_ca': ['f1'],
                'avis_renouvellement_mandat_recherche': ['f2'],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            EpreuveConfirmationNonTrouveeException.status_code,
        )

    def test_put_confirmation_promoter_without_supervisor_panel_report(self):
        self.client.force_authenticate(user=self.promoter)
        response = self.client.put(
            self.supervised_parcours_doctoral_url,
            format='json',
            data={
                'avis_renouvellement_mandat_recherche': [],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['proces_verbal_ca'][0],
            'Ce champ est obligatoire.',
        )


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class LastConfirmationAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Create supervision group members
        promoter = PromoterFactory()

        # Create parcours_doctoral management entity
        root = EntityVersionFactory(parent=None).entity
        sector = EntityVersionFactory(
            parent=root,
            entity_type=EntityType.SECTOR.name,
            acronym='SST',
        ).entity
        commission = EntityVersionFactory(
            parent=sector,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        ).entity
        cls.parcours_doctoral = ParcoursDoctoralFactory(
            status=ChoixStatutParcoursDoctoral.ADMITTED.name,
            training__management_entity=commission,
            supervision_group=promoter.process,
        )
        parcours_doctoral = ParcoursDoctoralFactory(
            training__management_entity=commission,
            student=cls.parcours_doctoral.student,
        )
        other_parcours_doctoral = ParcoursDoctoralFactory(
            status=ChoixStatutParcoursDoctoral.ADMITTED.name,
            training__management_entity=commission,
        )

        # Users
        cls.student = cls.parcours_doctoral.student
        cls.other_student = other_parcours_doctoral.student
        cls.manager = ProgramManagerFactory(education_group=cls.parcours_doctoral.training.education_group).person

        cls.parcours_doctoral_url = resolve_url('parcours_doctoral_api_v1:last_confirmation', uuid=cls.parcours_doctoral.uuid)
        cls.other_parcours_doctoral_url = resolve_url('parcours_doctoral_api_v1:last_confirmation', uuid=other_parcours_doctoral.uuid)
        cls.parcours_doctoral_url = resolve_url('parcours_doctoral_api_v1:last_confirmation', uuid=parcours_doctoral.uuid)

    def setUp(self):
        self.confirmation_papers = [
            ConfirmationPaperFactory(
                parcours_doctoral=self.parcours_doctoral,
                confirmation_date=datetime.date(2022, 4, 1),
                confirmation_deadline=datetime.date(2022, 4, 5),
            ),
            ConfirmationPaperFactory(
                parcours_doctoral=self.parcours_doctoral,
                confirmation_deadline=datetime.date(2022, 4, 10),
            ),
        ]

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.student.user)
        methods_not_allowed = [
            'delete',
            'patch',
        ]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.parcours_doctoral_url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_confirmation_student(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.parcours_doctoral_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        json_response = response.json()

        # Check the first confirmation paper
        self.assertEqual(json_response['uuid'], str(self.confirmation_papers[1].uuid))
        self.assertEqual(json_response['date_limite'], '2022-04-10')
        self.assertIsNone(json_response['date'])
        self.assertIsNone(json_response['demande_prolongation'])

    def test_get_confirmation_with_parcours_doctoral_invalid_status(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.parcours_doctoral_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_confirmation_with_parcours_doctoral_other_student(self):
        self.client.force_authenticate(user=self.other_student.user)
        response = self.client.get(self.parcours_doctoral_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_confirmation_student_invalid_date(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.put(
            self.parcours_doctoral_url,
            format='json',
            data={
                'date': '2022-05-15',
                'rapport_recherche': [],
                'proces_verbal_ca': [],
                'avis_renouvellement_mandat_recherche': [],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            EpreuveConfirmationDateIncorrecteException.status_code,
        )

    def test_put_confirmation_student_without_date(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.put(
            self.parcours_doctoral_url,
            format='json',
            data={
                'rapport_recherche': [],
                'proces_verbal_ca': [],
                'avis_renouvellement_mandat_recherche': [],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['date'][0],
            'Ce champ est obligatoire.',
        )

    @patch("osis_document.contrib.fields.FileField._confirm_multiple_upload")
    def test_put_confirmation_student(self, confirm_upload):
        confirmation_paper_uuid = self.confirmation_papers[1].uuid

        token = WriteTokenFactory()

        confirm_upload.side_effect = lambda _, value, __: [token.upload.uuid] if value else []

        self.client.force_authenticate(user=self.student.user)
        response = self.client.put(
            self.parcours_doctoral_url,
            format='json',
            data={
                'date': '2022-04-08',
                'rapport_recherche': [token.token],
                'proces_verbal_ca': [token.token],
                'avis_renouvellement_mandat_recherche': [token.token],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        self.assertEqual(response.json()['uuid'], str(self.parcours_doctoral.uuid))

        # Check the first confirmation paper
        confirmation_paper = ConfirmationPaper.objects.get(uuid=confirmation_paper_uuid)

        self.assertEqual(confirmation_paper.uuid, confirmation_paper_uuid)
        self.assertEqual(confirmation_paper.confirmation_deadline, datetime.date(2022, 4, 10))
        self.assertEqual(confirmation_paper.confirmation_date, datetime.date(2022, 4, 8))
        self.assertEqual(confirmation_paper.research_report, [token.upload.uuid])
        self.assertEqual(confirmation_paper.supervisor_panel_report, [token.upload.uuid])
        self.assertEqual(confirmation_paper.research_mandate_renewal_opinion, [token.upload.uuid])

        # Check the notifications
        self.assertEqual(WebNotification.objects.count(), 1)
        notification = WebNotification.objects.first()
        self.assertEqual(notification.person, self.manager)

    def test_put_confirmation_with_parcours_doctoral_invalid_status(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.put(
            self.parcours_doctoral_url,
            format='json',
            data={
                'date': '2022-05-15',
                'rapport_recherche': [],
                'proces_verbal_ca': [],
                'avis_renouvellement_mandat_recherche': [],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_confirmation_with_parcours_doctoral_other_student(self):
        self.client.force_authenticate(user=self.other_student.user)
        response = self.client.put(
            self.parcours_doctoral_url,
            format='json',
            data={
                'date': '2022-05-15',
                'rapport_recherche': [],
                'proces_verbal_ca': [],
                'avis_renouvellement_mandat_recherche': [],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_confirmation_with_parcours_doctoral_without_confirmation_paper(self):
        self.client.force_authenticate(user=self.other_student.user)
        response = self.client.put(
            self.other_parcours_doctoral_url,
            format='json',
            data={
                'date': '2022-05-15',
                'rapport_recherche': [],
                'proces_verbal_ca': [],
                'avis_renouvellement_mandat_recherche': [],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            EpreuveConfirmationNonTrouveeException.status_code,
        )

    def test_post_confirmation_student_without_new_date(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.post(
            self.parcours_doctoral_url,
            format='json',
            data={
                'justification_succincte': 'My reason',
                'lettre_justification': [],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['nouvelle_echeance'][0],
            'Ce champ est obligatoire.',
        )

    def test_post_confirmation_student_without_justification(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.post(
            self.parcours_doctoral_url,
            format='json',
            data={
                'nouvelle_echeance': '2022-05-15',
                'lettre_justification': [],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['justification_succincte'][0],
            'Ce champ est obligatoire.',
        )

    @patch("osis_document.contrib.fields.FileField._confirm_multiple_upload")
    def test_post_confirmation_student(self, confirm_upload):
        confirmation_paper_uuid = self.confirmation_papers[1].uuid

        token = WriteTokenFactory()

        confirm_upload.side_effect = lambda _, value, __: [token.upload.uuid] if value else []

        self.client.force_authenticate(user=self.student.user)
        response = self.client.post(
            self.parcours_doctoral_url,
            format='json',
            data={
                'nouvelle_echeance': '2022-05-15',
                'justification_succincte': 'My reason',
                'lettre_justification': [token.token],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        self.assertEqual(response.json()['uuid'], str(self.parcours_doctoral.uuid))

        # Check the first confirmation paper
        confirmation_paper: ConfirmationPaper = ConfirmationPaper.objects.get(uuid=confirmation_paper_uuid)

        self.assertEqual(confirmation_paper.uuid, confirmation_paper_uuid)
        self.assertEqual(confirmation_paper.extended_deadline, datetime.date(2022, 5, 15))
        self.assertEqual(confirmation_paper.brief_justification, 'My reason')
        self.assertEqual(confirmation_paper.justification_letter, [token.upload.uuid])

        # Check the notifications
        self.assertEqual(WebNotification.objects.count(), 1)
        notification = WebNotification.objects.first()
        self.assertEqual(notification.person, self.manager)

    def test_post_confirmation_with_parcours_doctoral_invalid_status(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.post(
            self.parcours_doctoral_url,
            format='json',
            data={
                'nouvelle_echeance': '2022-05-15',
                'justification_succincte': 'My reason',
                'lettre_justification': [],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_confirmation_with_parcours_doctoral_other_student(self):
        self.client.force_authenticate(user=self.other_student.user)
        response = self.client.post(
            self.parcours_doctoral_url,
            format='json',
            data={
                'nouvelle_echeance': '2022-05-15',
                'justification_succincte': 'My reason',
                'lettre_justification': [],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_confirmation_with_parcours_doctoral_without_confirmation_paper(self):
        self.client.force_authenticate(user=self.other_student.user)
        response = self.client.post(
            self.other_parcours_doctoral_url,
            format='json',
            data={
                'nouvelle_echeance': '2022-05-15',
                'justification_succincte': 'My reason',
                'lettre_justification': [],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            EpreuveConfirmationNonTrouveeException.status_code,
        )


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class LastConfirmationCanvasAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Create supervision group members
        promoter = PromoterFactory()

        # Create parcours_doctoral management entity
        root = EntityVersionFactory(parent=None).entity
        sector = EntityVersionFactory(
            parent=root,
            entity_type=EntityType.SECTOR.name,
            acronym='SST',
        ).entity

        commission = EntityVersionFactory(
            parent=sector,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        ).entity
        cls.parcours_doctoral = ParcoursDoctoralFactory(
            status=ChoixStatutParcoursDoctoral.ADMITTED.name,
        )
        parcours_doctoral = ParcoursDoctoralFactory(
            training__management_entity=commission,
            student=cls.parcours_doctoral.student,
        )
        other_parcours_doctoral = ParcoursDoctoralFactory(
            status=ChoixStatutParcoursDoctoral.ADMITTED.name,
            training__management_entity=commission,
        )

        # Users
        cls.student = cls.parcours_doctoral.student

        path_name = 'parcours_doctoral_api_v1:last_confirmation_canvas'
        cls.parcours_doctoral_url = resolve_url(path_name, uuid=cls.parcours_doctoral.uuid)
        cls.other_parcours_doctoral_url = resolve_url(path_name, uuid=other_parcours_doctoral.uuid)
        cls.parcours_doctoral_url = resolve_url(path_name, uuid=parcours_doctoral.uuid)

        # Mock osis-document
        cls.confirm_remote_upload_patcher = patch('osis_document.api.utils.confirm_remote_upload')
        patched = cls.confirm_remote_upload_patcher.start()
        patched.return_value = '4bdffb42-552d-415d-9e4c-725f10dce228'

        cls.confirm_remote_upload_patcher = patch('osis_document.contrib.fields.FileField._confirm_multiple_upload')
        patched = cls.confirm_remote_upload_patcher.start()
        patched.side_effect = lambda _, value, __: ['4bdffb42-552d-415d-9e4c-725f10dce228'] if value else []

        cls.get_remote_metadata_patcher = patch('osis_document.api.utils.get_remote_metadata')
        patched = cls.get_remote_metadata_patcher.start()
        patched.return_value = {"name": "test.pdf", "size": 1}

        cls.get_remote_token_patcher = patch('osis_document.api.utils.get_remote_token')
        patched = cls.get_remote_token_patcher.start()
        patched.return_value = 'b-token'

        cls.save_raw_content_remotely_patcher = patch('osis_document.utils.save_raw_content_remotely')
        patched = cls.save_raw_content_remotely_patcher.start()
        patched.return_value = 'a-token'

        # Mock weasyprint
        cls.get_pdf = patch('parcours_doctoral.exports.utils.get_pdf_from_template', return_value=b'some content')
        cls.get_pdf.start()

    @classmethod
    def tearDownClass(cls):
        cls.confirm_remote_upload_patcher.stop()
        cls.get_remote_metadata_patcher.stop()
        cls.get_remote_token_patcher.stop()
        cls.save_raw_content_remotely_patcher.stop()
        cls.get_pdf.stop()
        super().tearDownClass()

    def setUp(self):
        self.confirmation_paper = ConfirmationPaperFactory(
            parcours_doctoral=self.parcours_doctoral,
            confirmation_date=datetime.date(2022, 4, 1),
            confirmation_deadline=datetime.date(2022, 4, 5),
        )

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.student.user)
        methods_not_allowed = [
            'delete',
            'patch',
            'post',
            'put',
        ]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.parcours_doctoral_url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_confirmation_canvas_student(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.parcours_doctoral_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        json_response = response.json()
        self.assertEqual(json_response['uuid'], '4bdffb42-552d-415d-9e4c-725f10dce228')

        # Check saved data
        confirmation_paper = ConfirmationPaper.objects.get(uuid=self.confirmation_paper.uuid)
        self.assertEqual(
            confirmation_paper.supervisor_panel_report_canvas,
            [UUID('4bdffb42-552d-415d-9e4c-725f10dce228')],
        )

    def test_can_not_get_confirmation_canvas_if_not_parcours_doctoral(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.parcours_doctoral_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_can_not_get_confirmation_canvas_if_other_student(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.other_parcours_doctoral_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
