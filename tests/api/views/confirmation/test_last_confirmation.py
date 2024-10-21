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
from unittest import mock
from uuid import uuid4

import freezegun
from base.tests.factories.person import PersonFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from django.shortcuts import resolve_url
from osis_notification.models import WebNotification
from rest_framework import status
from rest_framework.test import APITestCase

from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.epreuve_confirmation.validators.exceptions import (
    EpreuveConfirmationDateIncorrecteException,
    EpreuveConfirmationNonTrouveeException,
)
from parcours_doctoral.models import ConfirmationPaper
from parcours_doctoral.tests.factories.confirmation_paper import (
    ConfirmationPaperFactory,
)
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.roles import StudentRoleFactory
from parcours_doctoral.tests.factories.supervision import (
    CaMemberFactory,
    PromoterFactory,
)


@freezegun.freeze_time('2023-01-01')
class LastConfirmationAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.file_uuids = {
            'research_report': uuid4(),
            'supervisor_panel_report': uuid4(),
            'supervisor_panel_report_canvas': uuid4(),
            'research_mandate_renewal_opinion': uuid4(),
            'certificate_of_achievement': uuid4(),
            'certificate_of_failure': uuid4(),
            'justification_letter': uuid4(),
        }

        # Users
        cls.student = StudentRoleFactory().person
        cls.other_student = StudentRoleFactory().person
        cls.no_role_user = PersonFactory().user
        promoter = PromoterFactory()
        cls.process = promoter.process
        cls.promoter_user = promoter.person.user
        cls.other_promoter_user = PromoterFactory().person.user
        cls.committee_member_user = CaMemberFactory(process=cls.process).person.user
        cls.other_committee_member_user = CaMemberFactory().person.user

        cls.doctorate = ParcoursDoctoralFactory(
            supervision_group=cls.process,
            student=cls.student,
            status=ChoixStatutParcoursDoctoral.ADMITTED.name,
        )

        cls.manager = ProgramManagerFactory(education_group=cls.doctorate.training.education_group).person

        cls.url = resolve_url('parcours_doctoral_api_v1:last_confirmation', uuid=cls.doctorate.uuid)

    def setUp(self):
        self.confirmation_paper: ConfirmationPaper = ConfirmationPaperFactory(
            parcours_doctoral=self.doctorate,
            confirmation_date=datetime.date(2022, 4, 1),
            confirmation_deadline=datetime.date(2022, 4, 5),
            research_report=[self.file_uuids['research_report']],
            supervisor_panel_report=[self.file_uuids['supervisor_panel_report']],
            supervisor_panel_report_canvas=[self.file_uuids['supervisor_panel_report_canvas']],
            research_mandate_renewal_opinion=[self.file_uuids['research_mandate_renewal_opinion']],
            certificate_of_achievement=[self.file_uuids['certificate_of_achievement']],
            certificate_of_failure=[self.file_uuids['certificate_of_failure']],
            extended_deadline=datetime.date(2023, 4, 6),
            brief_justification='Brief justification',
            justification_letter=[self.file_uuids['justification_letter']],
            cdd_opinion='CDD opinion',
        )

        patcher = mock.patch(
            "osis_document.contrib.fields.FileField._confirm_multiple_upload",
            side_effect=lambda _, value, __: value,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.student.user)
        methods_not_allowed = [
            'delete',
            'patch',
        ]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_last_confirmation_with_user_not_logged_is_forbidden(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.post(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.put(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_last_confirmation_with_user_with_no_role_is_forbidden(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.post(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_last_confirmation_with_student(self):
        self.client.force_authenticate(user=self.other_student.user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        confirmation_paper_json = response.json()

        self.assertEqual(confirmation_paper_json['uuid'], str(self.confirmation_paper.uuid))
        self.assertEqual(
            confirmation_paper_json['date_limite'],
            self.confirmation_paper.confirmation_deadline.isoformat(),
        )
        self.assertEqual(confirmation_paper_json['date'], self.confirmation_paper.confirmation_date.isoformat())
        self.assertEqual(
            confirmation_paper_json['rapport_recherche'],
            [str(self.confirmation_paper.research_report[0])],
        )
        self.assertEqual(
            confirmation_paper_json['demande_prolongation']['nouvelle_echeance'],
            self.confirmation_paper.extended_deadline.isoformat(),
        )
        self.assertEqual(
            confirmation_paper_json['demande_prolongation']['justification_succincte'],
            self.confirmation_paper.brief_justification,
        )
        self.assertEqual(
            confirmation_paper_json['demande_prolongation']['lettre_justification'],
            [str(self.confirmation_paper.justification_letter[0])],
        )
        self.assertEqual(
            confirmation_paper_json['demande_prolongation']['avis_cdd'],
            self.confirmation_paper.cdd_opinion,
        )
        self.assertEqual(
            confirmation_paper_json['proces_verbal_ca'],
            [str(self.confirmation_paper.supervisor_panel_report[0])],
        )
        self.assertEqual(
            confirmation_paper_json['attestation_reussite'],
            [str(self.confirmation_paper.certificate_of_achievement[0])],
        )
        self.assertEqual(
            confirmation_paper_json['attestation_echec'],
            [str(self.confirmation_paper.certificate_of_failure[0])],
        )
        self.assertEqual(
            confirmation_paper_json['canevas_proces_verbal_ca'],
            [str(self.confirmation_paper.supervisor_panel_report_canvas[0])],
        )
        self.assertEqual(
            confirmation_paper_json['avis_renouvellement_mandat_recherche'],
            [str(self.confirmation_paper.research_mandate_renewal_opinion[0])],
        )

    def test_last_confirmation_with_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.other_promoter_user)

        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.post(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_last_confirmation_with_ca_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.other_committee_member_user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.post(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_last_confirmation_with_no_confirmation_paper(self):
        self.client.force_login(user=self.student.user)

        self.confirmation_paper.delete()

        response = self.client.get(self.url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            EpreuveConfirmationNonTrouveeException.status_code,
        )

    def test_get_last_confirmation_with_several_confirmation_papers(self):
        self.client.force_authenticate(user=self.student.user)

        with freezegun.freeze_time('2023-04-01'):
            new_confirmation_paper = ConfirmationPaperFactory(
                parcours_doctoral=self.doctorate,
                confirmation_date=datetime.date(2023, 4, 1),
            )

        response = self.client.get(self.url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()

        self.assertEqual(json_response['uuid'], str(new_confirmation_paper.uuid))

    def test_update_last_confirmation(self):
        self.client.force_authenticate(user=self.student.user)

        self.confirmation_paper.research_report = []
        self.confirmation_paper.supervisor_panel_report = []
        self.confirmation_paper.research_mandate_renewal_opinion = []
        self.confirmation_paper.save()

        default_data = {
            'date': datetime.date(2022, 4, 4).isoformat(),
            'rapport_recherche': [str(self.file_uuids['research_report'])],
            'proces_verbal_ca': [str(self.file_uuids['supervisor_panel_report'])],
            'avis_renouvellement_mandat_recherche': [str(self.file_uuids['research_mandate_renewal_opinion'])],
        }

        response = self.client.put(
            self.url,
            data=default_data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.confirmation_paper.refresh_from_db()

        self.assertEqual(self.confirmation_paper.confirmation_date, datetime.date(2022, 4, 4))
        self.assertEqual(self.confirmation_paper.research_report, [self.file_uuids['research_report']])
        self.assertEqual(self.confirmation_paper.supervisor_panel_report, [self.file_uuids['supervisor_panel_report']])
        self.assertEqual(
            self.confirmation_paper.research_mandate_renewal_opinion,
            [self.file_uuids['research_mandate_renewal_opinion']],
        )

        # Check the notifications
        self.assertEqual(WebNotification.objects.count(), 1)
        notification = WebNotification.objects.first()
        self.assertEqual(notification.person, self.manager)

        self.confirmation_paper.delete()

        response = self.client.put(
            self.url,
            data=default_data,
            format='json',
        )

        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            EpreuveConfirmationNonTrouveeException.status_code,
        )

    def test_update_last_confirmation_with_invalid_date(self):
        self.client.force_authenticate(user=self.student.user)

        # Invalid date
        response = self.client.put(
            self.url,
            format='json',
            data={
                'date': datetime.date(2022, 5, 15).isoformat(),
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

    def test_submit_extension_request(self):
        self.client.force_authenticate(user=self.student.user)

        self.confirmation_paper.extended_deadline = None
        self.confirmation_paper.brief_justification = ''
        self.confirmation_paper.justification_letter = []
        self.confirmation_paper.save()

        default_data = {
            'nouvelle_echeance': datetime.date(2022, 4, 4).isoformat(),
            'justification_succincte': 'My reason',
            'lettre_justification': [str(self.file_uuids['justification_letter'])],
        }

        response = self.client.post(
            self.url,
            data=default_data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.confirmation_paper.refresh_from_db()

        self.assertEqual(self.confirmation_paper.extended_deadline, datetime.date(2022, 4, 4))
        self.assertEqual(self.confirmation_paper.brief_justification, 'My reason')
        self.assertEqual(self.confirmation_paper.justification_letter, [self.file_uuids['justification_letter']])

        # Check the notifications
        self.assertEqual(WebNotification.objects.count(), 1)
        notification = WebNotification.objects.first()
        self.assertEqual(notification.person, self.manager)

        self.confirmation_paper.delete()

        response = self.client.post(
            self.url,
            data=default_data,
            format='json',
        )

        self.assertEqual(
            response.json()['non_field_errors'][0]['status_code'],
            EpreuveConfirmationNonTrouveeException.status_code,
        )
