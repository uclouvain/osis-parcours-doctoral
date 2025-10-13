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
from unittest import mock
from uuid import uuid4

import freezegun
from django.shortcuts import resolve_url
from rest_framework import status
from rest_framework.test import APITestCase

from base.tests.factories.person import PersonFactory
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
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
class ConfirmationAPIViewTestCase(APITestCase):
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

    def setUp(self):
        patcher = mock.patch(
            "osis_document_components.fields.FileField._confirm_multiple_upload",
            side_effect=lambda _, value, __: value,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        self.doctorate = ParcoursDoctoralFactory(
            supervision_group=self.process,
            student=self.student,
        )
        self.url = resolve_url('parcours_doctoral_api_v1:confirmation', uuid=self.doctorate.uuid)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.student.user)
        methods_not_allowed = [
            'delete',
            'patch',
            'post',
            'put',
        ]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_confirmation_with_user_not_logged_is_forbidden(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_confirmation_with_user_with_no_role_is_forbidden(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_confirmation_with_invalid_enrolment_is_forbidden(self):
        in_creation_doctorate = ParcoursDoctoralFactory(
            supervision_group=self.doctorate.supervision_group,
            student=self.student,
            create_student__with_valid_enrolment=False,
        )

        url = resolve_url('parcours_doctoral_api_v1:confirmation', uuid=in_creation_doctorate.uuid)

        users = [
            self.promoter_user,
            self.committee_member_user,
            self.student.user,
        ]

        for user in users:
            self.client.force_authenticate(user=user)
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_confirmation_with_student(self):
        self.client.force_authenticate(user=self.other_student.user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()
        self.assertEqual(json_response, [])

    def test_get_confirmation_with_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_confirmation_with_ca_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.other_committee_member_user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_confirmation_with_several_confirmation_papers(self):
        self.client.force_authenticate(user=self.student.user)

        with freezegun.freeze_time('2022-01-01'):
            first_paper: ConfirmationPaper = ConfirmationPaperFactory(
                parcours_doctoral=self.doctorate,
                confirmation_date=datetime.date(2022, 4, 1),
                confirmation_deadline=datetime.date(2022, 4, 5),
                research_report=[self.file_uuids['research_report']],
                supervisor_panel_report=[self.file_uuids['supervisor_panel_report']],
                supervisor_panel_report_canvas=[self.file_uuids['supervisor_panel_report_canvas']],
                research_mandate_renewal_opinion=[self.file_uuids['research_mandate_renewal_opinion']],
                certificate_of_achievement=[self.file_uuids['certificate_of_achievement']],
                certificate_of_failure=[self.file_uuids['certificate_of_failure']],
                is_active=False,
            )

        with freezegun.freeze_time('2023-01-01'):
            second_paper: ConfirmationPaper = ConfirmationPaperFactory(
                parcours_doctoral=self.doctorate,
                confirmation_date=datetime.date(2023, 4, 1),
                confirmation_deadline=datetime.date(2023, 4, 5),
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
                is_active=True,
            )

        response = self.client.get(self.url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        json_response = response.json()

        self.assertEqual(len(json_response), 2)

        first_paper_json = json_response[1]
        second_paper_json = json_response[0]

        # Check the first confirmation paper
        self.assertEqual(first_paper_json['uuid'], str(first_paper.uuid))
        self.assertEqual(first_paper_json['date_limite'], first_paper.confirmation_deadline.isoformat())
        self.assertEqual(first_paper_json['date'], first_paper.confirmation_date.isoformat())
        self.assertEqual(first_paper_json['rapport_recherche'], [str(first_paper.research_report[0])])
        self.assertEqual(first_paper_json['demande_prolongation'], None)
        self.assertEqual(first_paper_json['proces_verbal_ca'], [str(first_paper.supervisor_panel_report[0])])
        self.assertEqual(first_paper_json['attestation_reussite'], [str(first_paper.certificate_of_achievement[0])])
        self.assertEqual(first_paper_json['attestation_echec'], [str(first_paper.certificate_of_failure[0])])
        self.assertEqual(
            first_paper_json['canevas_proces_verbal_ca'],
            [str(first_paper.supervisor_panel_report_canvas[0])],
        )
        self.assertEqual(
            first_paper_json['avis_renouvellement_mandat_recherche'],
            [str(first_paper.research_mandate_renewal_opinion[0])],
        )

        # Check the second confirmation paper
        self.assertEqual(second_paper_json['uuid'], str(second_paper.uuid))
        self.assertEqual(second_paper_json['date_limite'], second_paper.confirmation_deadline.isoformat())
        self.assertEqual(second_paper_json['date'], second_paper.confirmation_date.isoformat())
        self.assertEqual(second_paper_json['rapport_recherche'], [str(second_paper.research_report[0])])
        self.assertEqual(
            second_paper_json['demande_prolongation']['nouvelle_echeance'],
            second_paper.extended_deadline.isoformat(),
        )
        self.assertEqual(
            second_paper_json['demande_prolongation']['justification_succincte'],
            second_paper.brief_justification,
        )
        self.assertEqual(
            second_paper_json['demande_prolongation']['lettre_justification'],
            [str(second_paper.justification_letter[0])],
        )
        self.assertEqual(second_paper_json['demande_prolongation']['avis_cdd'], second_paper.cdd_opinion)
        self.assertEqual(second_paper_json['proces_verbal_ca'], [str(second_paper.supervisor_panel_report[0])])
        self.assertEqual(second_paper_json['attestation_reussite'], [str(second_paper.certificate_of_achievement[0])])
        self.assertEqual(second_paper_json['attestation_echec'], [str(second_paper.certificate_of_failure[0])])
        self.assertEqual(
            second_paper_json['canevas_proces_verbal_ca'],
            [str(second_paper.supervisor_panel_report_canvas[0])],
        )
        self.assertEqual(
            second_paper_json['avis_renouvellement_mandat_recherche'],
            [str(second_paper.research_mandate_renewal_opinion[0])],
        )
