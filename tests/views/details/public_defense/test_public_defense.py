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
from uuid import uuid4

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings

from admission.tests.factories.doctorate import DoctorateFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from parcours_doctoral.ddd.domain.model.enums import ChoixLangueDefense
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ENTITY_CDE
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.mixins import MockOsisDocumentMixin
from reference.tests.factories.language import LanguageFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class PublicDefenseDetailViewTestCase(MockOsisDocumentMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=cls.doctoral_commission, acronym=ENTITY_CDE)

        cls.training = DoctorateFactory()

        cls.student = PersonFactory()
        cls.manager = ProgramManagerFactory(education_group=cls.training.education_group).person

        cls.namespace = 'parcours_doctoral:public-defense'

    def setUp(self):
        super().setUp()

        self.doctorate = ParcoursDoctoralFactory(
            training=self.training,
            student=self.student,
            defense_language=LanguageFactory(),
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

    def test_with_valid_access(self):
        self.client.force_login(self.manager.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        doctorate = response.context.get('parcours_doctoral')

        self.doctorate.refresh_from_db()

        self.assertEqual(doctorate.langue_soutenance_publique, self.doctorate.defense_language.code)
        self.assertEqual(doctorate.nom_langue_soutenance_publique, self.doctorate.defense_language.name)
        self.assertEqual(doctorate.date_heure_soutenance_publique, self.doctorate.defense_datetime)
        self.assertEqual(doctorate.lieu_soutenance_publique, self.doctorate.defense_place)
        self.assertEqual(doctorate.local_deliberation, self.doctorate.defense_deliberation_room)
        self.assertEqual(
            doctorate.informations_complementaires_soutenance_publique,
            self.doctorate.defense_additional_information,
        )
        self.assertEqual(doctorate.resume_annonce, self.doctorate.announcement_summary)
        self.assertEqual(doctorate.photo_annonce, self.doctorate.announcement_photo)
        self.assertEqual(doctorate.proces_verbal_soutenance_publique, self.doctorate.defense_minutes)
        self.assertEqual(doctorate.date_retrait_diplome, self.doctorate.diploma_collection_date)
