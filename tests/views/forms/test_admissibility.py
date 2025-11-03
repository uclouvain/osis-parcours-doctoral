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

import freezegun
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings

from admission.tests.factories.doctorate import DoctorateFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ENTITY_CDE
from parcours_doctoral.ddd.jury.domain.model.enums import FormuleDefense
from parcours_doctoral.ddd.recevabilite.dtos import RecevabiliteDTO
from parcours_doctoral.tests.factories.admissibility import AdmissibilityFactory
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.mixins import MockOsisDocumentMixin


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class AdmissibilityFormViewTestCase(MockOsisDocumentMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=cls.doctoral_commission, acronym=ENTITY_CDE)

        cls.training = DoctorateFactory()

        cls.student = PersonFactory()
        cls.manager = ProgramManagerFactory(education_group=cls.training.education_group).person

        cls.detail_path = 'parcours_doctoral:admissibility'
        cls.update_path = 'parcours_doctoral:update:admissibility'

    def setUp(self):
        super().setUp()

        self.doctorate = ParcoursDoctoralFactory(
            training=self.training,
            student=self.student,
            defense_method=FormuleDefense.FORMULE_2.name,
        )

        self.update_url = resolve_url(self.update_path, uuid=self.doctorate.uuid)
        self.detail_url = resolve_url(self.detail_path, uuid=self.doctorate.uuid)

    def test_get_with_no_admissibility(self):
        self.client.force_login(self.manager.user)

        response = self.client.get(self.update_url)

        self.assertEqual(response.status_code, 200)

        current_admissibility = response.context.get('current_admissibility')
        all_admissibilities = response.context.get('all_admissibilities')
        supervisors = response.context.get('supervisors')

        self.assertIsNone(current_admissibility)
        self.assertEqual(all_admissibilities, [])
        self.assertEqual(len(supervisors), 2)

    def test_get_with_one_admissibility(self):
        self.client.force_login(self.manager.user)

        admissibility = AdmissibilityFactory(parcours_doctoral=self.doctorate)

        admissibility.refresh_from_db()

        response = self.client.get(self.update_url)

        self.assertEqual(response.status_code, 200)

        current_admissibility: Optional[RecevabiliteDTO] = response.context.get('current_admissibility')
        all_admissibilities = response.context.get('all_admissibilities')

        self.assertIsNotNone(current_admissibility)
        self.assertEqual(all_admissibilities, [current_admissibility])

        self.assertEqual(current_admissibility.uuid, str(admissibility.uuid))
        self.assertEqual(current_admissibility.parcours_doctoral_uuid, (str(self.doctorate.uuid)))
        self.assertEqual(current_admissibility.est_active, True)
        self.assertEqual(current_admissibility.date_decision, admissibility.decision_date)
        self.assertEqual(current_admissibility.avis_jury, admissibility.thesis_exam_board_opinion)
        self.assertEqual(current_admissibility.date_envoi_manuscrit, admissibility.manuscript_submission_date)
        self.assertEqual(current_admissibility.proces_verbal, admissibility.minutes)
        self.assertEqual(current_admissibility.canevas_proces_verbal, admissibility.minutes_canvas)

        form = response.context['form']

        self.assertEqual(
            form.initial,
            {
                'titre_these': self.doctorate.thesis_proposed_title,
                'date_decision': current_admissibility.date_decision,
                'avis_jury': current_admissibility.avis_jury,
                'date_envoi_manuscrit': current_admissibility.date_envoi_manuscrit,
                'proces_verbal': current_admissibility.proces_verbal,
            },
        )

    def test_get_with_several_admissibilities(self):
        self.client.force_login(self.manager.user)

        with freezegun.freeze_time('2025-01-01'):
            admissibility = AdmissibilityFactory(parcours_doctoral=self.doctorate)

        with freezegun.freeze_time('2024-01-01'):
            old_admissibility = AdmissibilityFactory(
                parcours_doctoral=self.doctorate,
                current_parcours_doctoral=None,
            )

        admissibility.refresh_from_db()
        old_admissibility.refresh_from_db()

        response = self.client.get(self.update_url)

        self.assertEqual(response.status_code, 200)

        current_admissibility: Optional[RecevabiliteDTO] = response.context.get('current_admissibility')
        all_admissibilities: list[RecevabiliteDTO] = response.context.get('all_admissibilities')

        self.assertIsNotNone(current_admissibility)

        self.assertEqual(current_admissibility.uuid, str(admissibility.uuid))
        self.assertEqual(current_admissibility.parcours_doctoral_uuid, (str(self.doctorate.uuid)))
        self.assertEqual(current_admissibility.est_active, True)
        self.assertEqual(current_admissibility.date_decision, admissibility.decision_date)
        self.assertEqual(current_admissibility.avis_jury, admissibility.thesis_exam_board_opinion)
        self.assertEqual(current_admissibility.date_envoi_manuscrit, admissibility.manuscript_submission_date)
        self.assertEqual(current_admissibility.proces_verbal, admissibility.minutes)
        self.assertEqual(current_admissibility.canevas_proces_verbal, admissibility.minutes_canvas)

        self.assertEqual(len(all_admissibilities), 2)

        other_admissibility = all_admissibilities[int(current_admissibility == all_admissibilities[0])]

        self.assertEqual(other_admissibility.uuid, str(old_admissibility.uuid))
        self.assertEqual(other_admissibility.parcours_doctoral_uuid, (str(self.doctorate.uuid)))
        self.assertEqual(other_admissibility.est_active, False)
        self.assertEqual(other_admissibility.avis_jury, old_admissibility.thesis_exam_board_opinion)
        self.assertEqual(other_admissibility.date_envoi_manuscrit, old_admissibility.manuscript_submission_date)
        self.assertEqual(other_admissibility.proces_verbal, old_admissibility.minutes)
        self.assertEqual(other_admissibility.canevas_proces_verbal, old_admissibility.minutes_canvas)

        form = response.context['form']

        self.assertEqual(
            form.initial,
            {
                'titre_these': self.doctorate.thesis_proposed_title,
                'date_decision': current_admissibility.date_decision,
                'avis_jury': current_admissibility.avis_jury,
                'date_envoi_manuscrit': current_admissibility.date_envoi_manuscrit,
                'proces_verbal': current_admissibility.proces_verbal,
            },
        )

    def test_post_with_valid_data(self):
        self.client.force_login(self.manager.user)

        admissibility = AdmissibilityFactory(
            parcours_doctoral=self.doctorate,
        )

        data = {
            'titre_these': 'Title 2',
            'date_decision': datetime.date(2026, 1, 1),
            'avis_jury_0': [uuid.uuid4()],
            'date_envoi_manuscrit': datetime.date(2025, 2, 2),
            'proces_verbal_0': [uuid.uuid4()],
        }

        response = self.client.post(self.update_url, data=data)

        self.assertRedirects(response=response, expected_url=self.detail_url, fetch_redirect_response=False)

        self.doctorate.refresh_from_db()

        self.assertEqual(self.doctorate.thesis_proposed_title, data['titre_these'])

        admissibility.refresh_from_db()

        self.assertEqual(admissibility.decision_date, data['date_decision'])
        self.assertEqual(admissibility.thesis_exam_board_opinion, data['avis_jury_0'])
        self.assertEqual(admissibility.manuscript_submission_date, data['date_envoi_manuscrit'])
        self.assertEqual(admissibility.minutes, data['proces_verbal_0'])
