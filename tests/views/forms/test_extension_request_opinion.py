# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime
import uuid

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from parcours_doctoral.models.confirmation_paper import ConfirmationPaper
from parcours_doctoral.tests.factories.confirmation_paper import (
    ConfirmationPaperFactory,
)
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.supervision import PromoterFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class ExtensionRequestOpinionFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        promoter = PromoterFactory()
        cls.promoter = promoter.person

        # Create parcours_doctorals
        cls.parcours_doctoral_without_confirmation_paper = ParcoursDoctoralFactory(
            training__academic_year=academic_years[0],
        )
        cls.parcours_doctoral_with_confirmation_papers = ParcoursDoctoralFactory(
            training=cls.parcours_doctoral_without_confirmation_paper.training,
        )

        # User with one cdd
        cls.manager = ProgramManagerFactory(
            education_group=cls.parcours_doctoral_without_confirmation_paper.training.education_group
        ).person.user
        cls.update_path = 'parcours_doctoral:update:extension-request-opinion'
        cls.read_path = 'parcours_doctoral:extension-request'

    def setUp(self):
        self.client.force_login(user=self.manager)
        self.confirmation_paper_with_extension_request = ConfirmationPaperFactory(
            parcours_doctoral=self.parcours_doctoral_with_confirmation_papers,
            confirmation_date=datetime.date(2022, 4, 1),
            confirmation_deadline=datetime.date(2022, 4, 5),
            extended_deadline=datetime.date(2023, 1, 1),
            cdd_opinion='My opinion',
            justification_letter=[],
            brief_justification='My reason',
        )

    def test_get_extension_request_opinion_form_cdd_user_with_unknown_parcours_doctoral(self):
        url = reverse(self.update_path, args=[uuid.uuid4()])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_get_extension_request_opinion_form_cdd_user_without_confirmation_paper(self):
        url = reverse(self.update_path, args=[self.parcours_doctoral_without_confirmation_paper.uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_get_extension_request_opinion_form_cdd_user_with_confirmation_paper_with_extension_request(self):
        url = reverse(self.update_path, args=[self.parcours_doctoral_with_confirmation_papers.uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)

        self.assertEqual(
            response.context.get('parcours_doctoral').uuid,
            str(self.parcours_doctoral_with_confirmation_papers.uuid),
        )
        self.assertEqual(
            response.context['form'].initial['avis_cdd'],
            'My opinion',
        )

    def test_get_extension_request_opinion_form_cdd_user_with_confirmation_paper_without_extension_request(self):
        self.confirmation_paper_with_extension_request.is_active = False
        self.confirmation_paper_with_extension_request.save()

        self.confirmation_paper_without_extension_request = ConfirmationPaperFactory(
            parcours_doctoral=self.parcours_doctoral_with_confirmation_papers,
            confirmation_date=datetime.date(2022, 6, 1),
            confirmation_deadline=datetime.date(2022, 6, 5),
        )

        url = reverse(self.update_path, args=[self.parcours_doctoral_with_confirmation_papers.uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)

        self.assertEqual(
            response.context.get('parcours_doctoral').uuid,
            str(self.parcours_doctoral_with_confirmation_papers.uuid),
        )
        self.assertEqual(response.context['form'].initial, {})

    def test_post_extension_request_opinion_form_cdd_user_with_confirmation_paper_with_extension_request(self):
        url = reverse(self.update_path, args=[self.parcours_doctoral_with_confirmation_papers.uuid])

        response = self.client.post(url, data={'avis_cdd': 'My new opinion'})

        self.assertRedirects(
            response, resolve_url(self.read_path, uuid=self.parcours_doctoral_with_confirmation_papers.uuid)
        )

        updated_confirmation_paper = ConfirmationPaper.objects.get(
            uuid=self.confirmation_paper_with_extension_request.uuid,
        )
        self.assertEqual(updated_confirmation_paper.cdd_opinion, 'My new opinion')

    def test_post_extension_request_opinion_form_cdd_user_with_confirmation_paper_without_extension_request(self):
        self.confirmation_paper_with_extension_request.is_active = False
        self.confirmation_paper_with_extension_request.save()

        self.confirmation_paper_without_extension_request = ConfirmationPaperFactory(
            parcours_doctoral=self.parcours_doctoral_with_confirmation_papers,
            confirmation_date=datetime.date(2022, 6, 1),
            confirmation_deadline=datetime.date(2022, 6, 5),
        )

        url = reverse(self.update_path, kwargs={'uuid': self.parcours_doctoral_with_confirmation_papers.uuid})

        response = self.client.post(url, data={'avis_cdd': 'My new opinion'})

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(
            response.wsgi_request.path,
            resolve_url(self.update_path, uuid=self.parcours_doctoral_with_confirmation_papers.uuid),
        )
        self.assertFormError(response.context['form'], None, ['Demande de prolongation non définie.'])
