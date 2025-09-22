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

from typing import Optional

import freezegun
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
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.private_defense import PrivateDefenseFactory
from parcours_doctoral.tests.mixins import MockOsisDocumentMixin


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class PrivateDefenseDetailViewTestCase(MockOsisDocumentMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=cls.doctoral_commission, acronym=ENTITY_CDE)

        cls.training = DoctorateFactory()

        cls.student = PersonFactory()
        cls.manager = ProgramManagerFactory(education_group=cls.training.education_group).person

        cls.namespace = 'parcours_doctoral:private-defense'

    def setUp(self):
        super().setUp()

        self.doctorate = ParcoursDoctoralFactory(
            training=self.training,
            student=self.student,
        )

        self.url = resolve_url(self.namespace, uuid=self.doctorate.uuid)

    def test_with_no_private_defense(self):
        self.client.force_login(self.manager.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        current_private_defense = response.context.get('current_private_defense')
        all_private_defenses = response.context.get('all_private_defenses')
        supervision = response.context.get('supervision')

        self.assertIsNone(current_private_defense)
        self.assertEqual(all_private_defenses, [])
        self.assertIsNotNone(supervision)

    def test_with_one_private_defense(self):
        self.client.force_login(self.manager.user)

        private_defense = PrivateDefenseFactory(parcours_doctoral=self.doctorate)

        private_defense.refresh_from_db()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        current_private_defense: Optional[DefensePriveeDTO] = response.context.get('current_private_defense')
        all_private_defenses = response.context.get('all_private_defenses')

        self.assertIsNotNone(current_private_defense)
        self.assertEqual(all_private_defenses, [current_private_defense])

        self.assertEqual(current_private_defense.uuid, str(private_defense.uuid))
        self.assertEqual(current_private_defense.parcours_doctoral_uuid, (str(self.doctorate.uuid)))
        self.assertEqual(current_private_defense.est_active, True)
        self.assertEqual(current_private_defense.titre_these, self.doctorate.thesis_proposed_title)
        self.assertEqual(current_private_defense.date_heure, private_defense.datetime)
        self.assertEqual(current_private_defense.lieu, private_defense.place)
        self.assertEqual(current_private_defense.date_envoi_manuscrit, private_defense.manuscript_submission_date)
        self.assertEqual(current_private_defense.proces_verbal, private_defense.minutes)
        self.assertEqual(current_private_defense.canevas_proces_verbal, private_defense.minutes_canvas)

    def test_with_several_private_defenses(self):
        self.client.force_login(self.manager.user)

        with freezegun.freeze_time('2025-01-01'):
            private_defense = PrivateDefenseFactory(parcours_doctoral=self.doctorate)

        with freezegun.freeze_time('2024-01-01'):
            old_private_defense = PrivateDefenseFactory(
                parcours_doctoral=self.doctorate,
                current_parcours_doctoral=None,
            )

        private_defense.refresh_from_db()
        old_private_defense.refresh_from_db()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        current_private_defense: Optional[DefensePriveeDTO] = response.context.get('current_private_defense')
        all_private_defenses: list[DefensePriveeDTO] = response.context.get('all_private_defenses')

        self.assertIsNotNone(current_private_defense)

        self.assertEqual(current_private_defense.uuid, str(private_defense.uuid))
        self.assertEqual(current_private_defense.parcours_doctoral_uuid, (str(self.doctorate.uuid)))
        self.assertEqual(current_private_defense.est_active, True)
        self.assertEqual(current_private_defense.titre_these, self.doctorate.thesis_proposed_title)
        self.assertEqual(current_private_defense.date_heure, private_defense.datetime)
        self.assertEqual(current_private_defense.lieu, private_defense.place)
        self.assertEqual(current_private_defense.date_envoi_manuscrit, private_defense.manuscript_submission_date)
        self.assertEqual(current_private_defense.proces_verbal, private_defense.minutes)
        self.assertEqual(current_private_defense.canevas_proces_verbal, private_defense.minutes_canvas)

        self.assertEqual(len(all_private_defenses), 2)

        other_private_defense = all_private_defenses[int(current_private_defense == all_private_defenses[0])]

        self.assertEqual(other_private_defense.uuid, str(old_private_defense.uuid))
        self.assertEqual(other_private_defense.parcours_doctoral_uuid, (str(self.doctorate.uuid)))
        self.assertEqual(other_private_defense.est_active, False)
        self.assertEqual(other_private_defense.titre_these, self.doctorate.thesis_proposed_title)
        self.assertEqual(other_private_defense.date_heure, old_private_defense.datetime)
        self.assertEqual(other_private_defense.lieu, old_private_defense.place)
        self.assertEqual(other_private_defense.date_envoi_manuscrit, old_private_defense.manuscript_submission_date)
        self.assertEqual(other_private_defense.proces_verbal, old_private_defense.minutes)
        self.assertEqual(other_private_defense.canevas_proces_verbal, old_private_defense.minutes_canvas)
