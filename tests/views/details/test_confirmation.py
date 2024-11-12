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
from typing import List, Optional

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status

from parcours_doctoral.ddd.domain.model.doctorat_formation import ENTITY_CDE, ENTITY_CDSS
from parcours_doctoral.tests.factories.supervision import PromoterFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from parcours_doctoral.tests.factories.confirmation_paper import ConfirmationPaperFactory
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class ConfirmationDetailViewTestCase(TestCase):
    parcours_doctoral_with_confirmation_papers = Optional[ParcoursDoctoralFactory]
    parcours_doctoral_without_confirmation_paper = Optional[ParcoursDoctoralFactory]
    confirmation_papers = List[ConfirmationPaperFactory]

    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        # First entity
        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)

        second_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=second_doctoral_commission, acronym=ENTITY_CDSS)

        promoter = PromoterFactory()
        cls.promoter = promoter.person

        # Create parcours_doctorals
        cls.parcours_doctoral_without_confirmation_paper = ParcoursDoctoralFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
        )
        cls.parcours_doctoral_with_confirmation_papers = ParcoursDoctoralFactory(
            training=cls.parcours_doctoral_without_confirmation_paper.training,
        )
        cls.confirmation_papers = [
            ConfirmationPaperFactory(
                parcours_doctoral=cls.parcours_doctoral_with_confirmation_papers,
                confirmation_date=datetime.date(2022, 4, 1),
                confirmation_deadline=datetime.date(2022, 4, 5),
            ),
            ConfirmationPaperFactory(
                parcours_doctoral=cls.parcours_doctoral_with_confirmation_papers,
                confirmation_deadline=datetime.date(2022, 4, 5),
            ),
        ]

        cls.student = cls.parcours_doctoral_without_confirmation_paper.student

        cls.manager = ProgramManagerFactory(
            education_group=cls.parcours_doctoral_without_confirmation_paper.training.education_group
        ).person

    def test_confirmation_detail_cdd_user_without_confirmation_paper(self):
        self.client.force_login(user=self.manager.user)

        url = reverse('parcours_doctoral:confirmation', args=[self.parcours_doctoral_without_confirmation_paper.uuid])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNotNone(response.context.get('parcours_doctoral'))
        self.assertEqual(response.context.get('parcours_doctoral').uuid, str(self.parcours_doctoral_without_confirmation_paper.uuid))

        self.assertIsNone(response.context.get('current_confirmation_paper'))
        self.assertEqual(response.context.get('previous_confirmation_papers'), [])

    def test_confirmation_detail_cdd_user_with_confirmation_papers(self):
        self.client.force_login(user=self.manager.user)

        url = reverse('parcours_doctoral:confirmation', args=[self.parcours_doctoral_with_confirmation_papers.uuid])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.context.get('parcours_doctoral').uuid, str(self.parcours_doctoral_with_confirmation_papers.uuid))

        self.assertIsNotNone(response.context.get('current_confirmation_paper'))
        self.assertEqual(response.context.get('current_confirmation_paper').uuid, str(self.confirmation_papers[1].uuid))
        self.assertEqual(len(response.context.get('previous_confirmation_papers')), 1)
        self.assertEqual(
            response.context.get('previous_confirmation_papers')[0].uuid,
            str(self.confirmation_papers[0].uuid),
        )
