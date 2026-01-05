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

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings

from admission.tests.factories.doctorate import DoctorateFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.enums import (
    ChoixStatutAutorisationDiffusionThese,
    TypeModalitesDiffusionThese,
)
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ENTITY_CDE
from parcours_doctoral.ddd.jury.domain.model.enums import FormuleDefense
from parcours_doctoral.models import ParcoursDoctoral
from parcours_doctoral.models.thesis_distribution_authorization import (
    ThesisDistributionAuthorization,
)
from parcours_doctoral.tests.factories.authorization_distribution import (
    ThesisDistributionAuthorizationFactory,
)
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.roles import AdreManagerRoleFactory
from parcours_doctoral.tests.mixins import MockOsisDocumentMixin


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class AuthorizationDistributionDetailViewTestCase(MockOsisDocumentMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=cls.doctoral_commission, acronym=ENTITY_CDE)

        cls.training = DoctorateFactory()

        cls.student = PersonFactory()
        cls.manager = ProgramManagerFactory(education_group=cls.training.education_group).person
        cls.adre_manager = AdreManagerRoleFactory().person

        cls.namespace = 'parcours_doctoral:authorization-distribution'

    def setUp(self):
        super().setUp()

        self.doctorate: ParcoursDoctoral = ParcoursDoctoralFactory(
            student=self.student,
            status=ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_REUSSIE.name,
            defense_method=FormuleDefense.FORMULE_1.name,
        )
        self.thesis_distribution_authorization: ThesisDistributionAuthorization = (
            ThesisDistributionAuthorizationFactory(
                parcours_doctoral=self.doctorate,
                status=ChoixStatutAutorisationDiffusionThese.DIFFUSION_NON_SOUMISE.name,
                funding_sources='Funding sources',
                thesis_summary_in_english='Summary in english',
                thesis_summary_in_other_language='Summary in other language',
                thesis_keywords=['word1', 'word2'],
                conditions=TypeModalitesDiffusionThese.ACCES_EMBARGO.name,
                embargo_date=datetime.date(2025, 1, 15),
                additional_limitation_for_specific_chapters='Additional limitation',
                accepted_on=datetime.date(2026, 2, 3),
                acceptation_content='Accepted content',
            )
        )

        self.url = resolve_url(self.namespace, uuid=self.doctorate.uuid)

    def test_with_valid_access(self):
        self.client.force_login(self.adre_manager.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        authorization_distribution = response.context.get('authorization_distribution')

        self.thesis_distribution_authorization.refresh_from_db()

        self.assertEqual(
            authorization_distribution.statut,
            ChoixStatutAutorisationDiffusionThese.DIFFUSION_NON_SOUMISE.name,
        )
        self.assertEqual(authorization_distribution.sources_financement, 'Funding sources')
        self.assertEqual(authorization_distribution.resume_anglais, 'Summary in english')
        self.assertEqual(authorization_distribution.resume_autre_langue, 'Summary in other language')
        self.assertEqual(authorization_distribution.mots_cles, ['word1', 'word2'])
        self.assertEqual(
            authorization_distribution.type_modalites_diffusion,
            TypeModalitesDiffusionThese.ACCES_EMBARGO.name,
        )
        self.assertEqual(authorization_distribution.date_embargo, datetime.date(2025, 1, 15))
        self.assertEqual(authorization_distribution.limitations_additionnelles_chapitres, 'Additional limitation')
        self.assertEqual(authorization_distribution.modalites_diffusion_acceptees_le, datetime.date(2026, 2, 3))
        self.assertEqual(authorization_distribution.signataires, [])
