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
import uuid
from uuid import uuid4

from django.conf import settings
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings

from admission.tests.factories.doctorate import DoctorateFactory
from base.forms.utils import EMPTY_CHOICE
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ENTITY_CDE
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.mixins import MockOsisDocumentMixin
from reference.models.language import Language
from reference.tests.factories.language import LanguageFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class PublicDefenseFormViewTestCase(MockOsisDocumentMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=cls.doctoral_commission, acronym=ENTITY_CDE)

        cls.training = DoctorateFactory()

        cls.student = PersonFactory()
        cls.manager = ProgramManagerFactory(
            education_group=cls.training.education_group,
            person__language=settings.LANGUAGE_CODE_EN,
        ).person

        cls.a_language = LanguageFactory(name='A')
        cls.b_language = LanguageFactory(name='B')

        cls.namespace = 'parcours_doctoral:update:public-defense'
        cls.detail_namespace = 'parcours_doctoral:public-defense'

    def setUp(self):
        super().setUp()

        self.doctorate = ParcoursDoctoralFactory(
            training=self.training,
            student=self.student,
            defense_language=self.a_language,
            defense_datetime=datetime.datetime(2025, 1, 5, 11, 30),
            defense_place='Louvain-La-Neuve',
            defense_deliberation_room='D1',
            defense_additional_information='Additional information',
            announcement_summary='Announcement summary',
            announcement_photo=[uuid4()],
            defense_minutes=[uuid4()],
            defense_minutes_canvas=[uuid4()],
            diploma_collection_date=datetime.date(2026, 1, 6),
        )

        self.url = resolve_url(self.namespace, uuid=self.doctorate.uuid)
        self.detail_url = resolve_url(self.detail_namespace, uuid=self.doctorate.uuid)

    def test_get_form(self):
        self.client.force_login(self.manager.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(form.initial['langue'], self.doctorate.defense_language.code)
        self.assertEqual(form.initial['date_heure'], self.doctorate.defense_datetime)
        self.assertEqual(form.initial['lieu'], self.doctorate.defense_place)
        self.assertEqual(form.initial['local_deliberation'], self.doctorate.defense_deliberation_room)
        self.assertEqual(form.initial['informations_complementaires'], self.doctorate.defense_additional_information)
        self.assertEqual(form.initial['resume_annonce'], self.doctorate.announcement_summary)
        self.assertEqual(form.initial['photo_annonce'], self.doctorate.announcement_photo)
        self.assertEqual(form.initial['proces_verbal'], self.doctorate.defense_minutes)
        self.assertEqual(form.initial['date_retrait_diplome'], self.doctorate.diploma_collection_date)

        self.assertEqual(
            form.fields['langue'].choices,
            [
                EMPTY_CHOICE[0],
                *[(language.code, language.name) for language in Language.objects.all().order_by('name')],
            ],
        )

    def test_post_form(self):
        self.client.force_login(self.manager.user)

        new_data = {
            'langue': self.b_language.code,
            'date_heure_0': '01/01/2026',
            'date_heure_1': '11:00',
            'lieu': 'Mons',
            'local_deliberation': 'D2',
            'informations_complementaires': 'New information',
            'resume_annonce': 'New summary',
            'photo_annonce_0': [uuid.uuid4()],
            'proces_verbal_0': [uuid.uuid4()],
            'date_retrait_diplome': datetime.date(2027, 2, 1),
        }

        response = self.client.post(self.url, data=new_data)

        self.assertRedirects(
            response=response,
            expected_url=self.detail_url,
            fetch_redirect_response=False,
        )

        self.doctorate.refresh_from_db()

        self.assertEqual(new_data['langue'], self.doctorate.defense_language.code)
        self.assertEqual(datetime.datetime(2026, 1, 1, 11), self.doctorate.defense_datetime)
        self.assertEqual(new_data['lieu'], self.doctorate.defense_place)
        self.assertEqual(new_data['local_deliberation'], self.doctorate.defense_deliberation_room)
        self.assertEqual(new_data['informations_complementaires'], self.doctorate.defense_additional_information)
        self.assertEqual(new_data['resume_annonce'], self.doctorate.announcement_summary)
        self.assertEqual(new_data['photo_annonce_0'], self.doctorate.announcement_photo)
        self.assertEqual(new_data['proces_verbal_0'], self.doctorate.defense_minutes)
        self.assertEqual(new_data['date_retrait_diplome'], self.doctorate.diploma_collection_date)
