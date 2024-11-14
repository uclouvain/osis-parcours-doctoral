# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.test import TestCase
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from parcours_doctoral.tests.factories.supervision import PromoterFactory
from parcours_doctoral.ddd.jury.domain.model.enums import FormuleDefense, ChoixLangueRedactionThese
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from parcours_doctoral.models.parcours_doctoral import ParcoursDoctoral
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from reference.tests.factories.language import FrenchLanguageFactory


class JuryFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        promoter = PromoterFactory()
        cls.promoter = promoter.person

        # Create parcours_doctorals
        cls.parcours_doctoral = ParcoursDoctoralFactory(
            training__academic_year=academic_years[0],
        )

        # User with one cdd
        cls.manager = ProgramManagerFactory(education_group=cls.parcours_doctoral.training.education_group).person.user
        cls.update_path = 'parcours_doctoral:update:jury-preparation'
        cls.read_path = 'parcours_doctoral:jury-preparation'

    def setUp(self):
        self.client.force_login(user=self.manager)

    def test_get_jury_preparation_detail_cdd_user_with_unknown_parcours_doctoral(self):
        url = reverse(self.update_path, args=[uuid.uuid4()])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_get_jury_preparation_detail_cdd_user(self):
        url = reverse(self.update_path, args=[self.parcours_doctoral.uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)

        self.assertEqual(
            response.context.get('parcours_doctoral').uuid,
            str(self.parcours_doctoral.uuid),
        )
        self.assertEqual(
            response.context['form'].initial,
            {
                'titre_propose': self.parcours_doctoral.thesis_proposed_title,
                'formule_defense': self.parcours_doctoral.defense_method,
                'date_indicative': self.parcours_doctoral.defense_indicative_date.isoformat()
                if self.parcours_doctoral.defense_indicative_date
                else None,
                'langue_redaction': self.parcours_doctoral.thesis_language,
                'langue_soutenance': self.parcours_doctoral.defense_language,
                'commentaire': self.parcours_doctoral.comment_about_jury,
            },
        )

    def test_post_jury_preparation_detail_cdd_user(self):
        url = reverse(self.update_path, args=[self.parcours_doctoral.uuid])
        language = FrenchLanguageFactory()

        response = self.client.post(
            url,
            data={
                'titre_propose': 'Nouveau titre',
                'formule_defense': FormuleDefense.FORMULE_2.name,
                'date_indicative': '01/01/2023',
                'langue_redaction': language.pk,
                'langue_soutenance': ChoixLangueRedactionThese.ENGLISH.name,
                'commentaire': 'Nouveau commentaire',
            },
        )

        self.assertRedirects(response, resolve_url(self.read_path, uuid=self.parcours_doctoral.uuid))

        updated_parcours_doctoral = ParcoursDoctoral.objects.get(
            uuid=self.parcours_doctoral.uuid,
        )
        self.assertEqual(updated_parcours_doctoral.thesis_proposed_title, 'Nouveau titre')
        self.assertEqual(updated_parcours_doctoral.defense_method, FormuleDefense.FORMULE_2.name)
        self.assertEqual(updated_parcours_doctoral.defense_indicative_date, datetime.date(2023, 1, 1))
        self.assertEqual(updated_parcours_doctoral.thesis_language, language)
        self.assertEqual(updated_parcours_doctoral.defense_language, ChoixLangueRedactionThese.ENGLISH.name)
        self.assertEqual(updated_parcours_doctoral.comment_about_jury, 'Nouveau commentaire')
