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
from typing import Optional

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings

from admission.tests.factories.doctorate import DoctorateFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from parcours_doctoral.ddd.defense_privee.dtos import DefensePriveeDTO
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ENTITY_CDE
from parcours_doctoral.ddd.jury.domain.model.enums import FormuleDefense
from parcours_doctoral.models import ParcoursDoctoral
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.private_defense import PrivateDefenseFactory
from parcours_doctoral.tests.mixins import MockOsisDocumentMixin
from reference.tests.factories.language import LanguageFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class PrivatePublicDefensesFormViewTestCase(MockOsisDocumentMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=cls.doctoral_commission, acronym=ENTITY_CDE)

        cls.training = DoctorateFactory()

        cls.a_language = LanguageFactory(name='A')
        cls.b_language = LanguageFactory(name='B')

        cls.student = PersonFactory()
        cls.manager = ProgramManagerFactory(education_group=cls.training.education_group).person

        cls.detail_path = 'parcours_doctoral:private-public-defenses'
        cls.update_path = 'parcours_doctoral:update:private-public-defenses'

    def setUp(self):
        super().setUp()

        self.doctorate: ParcoursDoctoral = ParcoursDoctoralFactory(
            training=self.training,
            student=self.student,
            defense_method=FormuleDefense.FORMULE_2.name,
            defense_language=self.a_language,
            defense_datetime=datetime.datetime(2025, 1, 5, 11, 30),
            defense_place='Louvain-La-Neuve',
            defense_deliberation_room='D1',
            defense_additional_information='Additional information',
            announcement_summary='Announcement summary',
            announcement_photo=[uuid.uuid4()],
            defense_minutes=[uuid.uuid4()],
            defense_minutes_canvas=[uuid.uuid4()],
            diploma_collection_date=datetime.date(2026, 1, 6),
        )

        self.update_url = resolve_url(self.update_path, uuid=self.doctorate.uuid)
        self.detail_url = resolve_url(self.detail_path, uuid=self.doctorate.uuid)

    def test_get_with_no_private_defense(self):
        self.client.force_login(self.manager.user)

        response = self.client.get(self.update_url)

        self.assertEqual(response.status_code, 200)

        current_private_defense = response.context.get('current_private_defense')
        all_private_defenses = response.context.get('all_private_defenses')
        supervisors = response.context.get('supervisors')

        self.assertIsNone(current_private_defense)
        self.assertEqual(all_private_defenses, [])
        self.assertEqual(len(supervisors), 2)

        form = response.context['form']

        self.assertEqual(
            form.initial,
            {
                'titre_these': self.doctorate.thesis_proposed_title,
                'langue_soutenance_publique': self.doctorate.defense_language.code,
                'date_heure_soutenance_publique': self.doctorate.defense_datetime,
                'lieu_soutenance_publique': self.doctorate.defense_place,
                'local_deliberation': self.doctorate.defense_deliberation_room,
                'informations_complementaires': self.doctorate.defense_additional_information,
                'resume_annonce': self.doctorate.announcement_summary,
                'photo_annonce': self.doctorate.announcement_photo,
                'proces_verbal_soutenance_publique': self.doctorate.defense_minutes,
                'date_retrait_diplome': self.doctorate.diploma_collection_date,
            },
        )

    def test_get_with_one_private_defense(self):
        self.client.force_login(self.manager.user)

        private_defense = PrivateDefenseFactory(parcours_doctoral=self.doctorate)

        private_defense.refresh_from_db()

        response = self.client.get(self.update_url)

        self.assertEqual(response.status_code, 200)

        current_private_defense: Optional[DefensePriveeDTO] = response.context.get('current_private_defense')
        all_private_defenses = response.context.get('all_private_defenses')

        self.assertIsNotNone(current_private_defense)
        self.assertEqual(all_private_defenses, [current_private_defense])

        self.assertEqual(current_private_defense.uuid, str(private_defense.uuid))
        self.assertEqual(current_private_defense.parcours_doctoral_uuid, (str(self.doctorate.uuid)))
        self.assertEqual(current_private_defense.est_active, True)
        self.assertEqual(current_private_defense.date_heure, private_defense.datetime)
        self.assertEqual(current_private_defense.lieu, private_defense.place)
        self.assertEqual(current_private_defense.date_envoi_manuscrit, private_defense.manuscript_submission_date)
        self.assertEqual(current_private_defense.proces_verbal, private_defense.minutes)
        self.assertEqual(current_private_defense.canevas_proces_verbal, private_defense.minutes_canvas)

        form = response.context['form']

        self.assertEqual(
            form.initial,
            {
                'titre_these': self.doctorate.thesis_proposed_title,
                'date_heure_defense_privee': current_private_defense.date_heure,
                'lieu_defense_privee': current_private_defense.lieu,
                'date_envoi_manuscrit': current_private_defense.date_envoi_manuscrit,
                'proces_verbal_defense_privee': current_private_defense.proces_verbal,
                'langue_soutenance_publique': self.doctorate.defense_language.code,
                'date_heure_soutenance_publique': self.doctorate.defense_datetime,
                'lieu_soutenance_publique': self.doctorate.defense_place,
                'local_deliberation': self.doctorate.defense_deliberation_room,
                'informations_complementaires': self.doctorate.defense_additional_information,
                'resume_annonce': self.doctorate.announcement_summary,
                'photo_annonce': self.doctorate.announcement_photo,
                'proces_verbal_soutenance_publique': self.doctorate.defense_minutes,
                'date_retrait_diplome': self.doctorate.diploma_collection_date,
            },
        )

    def test_post_with_valid_data(self):
        self.client.force_login(self.manager.user)

        private_defense = PrivateDefenseFactory(parcours_doctoral=self.doctorate)

        data = {
            'titre_these': 'Title 2',
            'date_heure_defense_privee_0': '01/01/2026',
            'date_heure_defense_privee_1': '11:00',
            'lieu_defense_privee': 'L2',
            'date_envoi_manuscrit': datetime.date(2025, 2, 2),
            'proces_verbal_defense_privee_0': [uuid.uuid4()],
            'langue_soutenance_publique': self.b_language.code,
            'date_heure_soutenance_publique_0': '02/01/2026',
            'date_heure_soutenance_publique_1': '12:00',
            'lieu_soutenance_publique': 'Mons',
            'local_deliberation': 'D2',
            'informations_complementaires': 'New information',
            'resume_annonce': 'New summary',
            'photo_annonce_0': [uuid.uuid4()],
            'proces_verbal_soutenance_publique_0': [uuid.uuid4()],
            'date_retrait_diplome': datetime.date(2027, 2, 1),
        }

        response = self.client.post(self.update_url, data=data)

        self.assertRedirects(response=response, expected_url=self.detail_url, fetch_redirect_response=False)

        self.doctorate.refresh_from_db()

        self.assertEqual(self.doctorate.thesis_proposed_title, data['titre_these'])
        self.assertEqual(self.doctorate.defense_language.code, data['langue_soutenance_publique'])
        self.assertEqual(self.doctorate.defense_datetime, datetime.datetime(2026, 1, 2, 12))
        self.assertEqual(self.doctorate.defense_place, data['lieu_soutenance_publique'])
        self.assertEqual(self.doctorate.defense_deliberation_room, data['local_deliberation'])
        self.assertEqual(self.doctorate.defense_additional_information, data['informations_complementaires'])
        self.assertEqual(self.doctorate.announcement_summary, data['resume_annonce'])
        self.assertEqual(self.doctorate.announcement_photo, data['photo_annonce_0'])
        self.assertEqual(self.doctorate.defense_minutes, data['proces_verbal_soutenance_publique_0'])
        self.assertEqual(self.doctorate.diploma_collection_date, data['date_retrait_diplome'])

        private_defense.refresh_from_db()

        self.assertEqual(private_defense.datetime, datetime.datetime(2026, 1, 1, 11))
        self.assertEqual(private_defense.place, data['lieu_defense_privee'])
        self.assertEqual(private_defense.manuscript_submission_date, data['date_envoi_manuscrit'])
        self.assertEqual(private_defense.minutes, data['proces_verbal_defense_privee_0'])
