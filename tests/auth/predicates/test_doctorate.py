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

from unittest import mock

from base.tests.factories.entity import EntityFactory
from django.test import TestCase

from parcours_doctoral.auth.predicates import (
    parcours_doctoral as parcours_doctoral_predicates,
)
from parcours_doctoral.auth.roles.cdd_configurator import CddConfigurator
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.roles import CddConfiguratorFactory


class PredicatesTestCase(TestCase):
    def setUp(self):
        self.predicate_context_patcher = mock.patch(
            "rules.Predicate.context",
            new_callable=mock.PropertyMock,
            return_value={'perm_name': 'dummy-perm'},
        )
        self.predicate_context_patcher.start()
        self.addCleanup(self.predicate_context_patcher.stop)

    def test_is_part_of_doctoral_commission(self):
        doctoral_commission = EntityFactory()
        request = ParcoursDoctoralFactory(training__management_entity=doctoral_commission)
        manager1 = CddConfiguratorFactory(entity=doctoral_commission)
        manager2 = CddConfiguratorFactory()

        self.predicate_context_patcher.target.context['role_qs'] = CddConfigurator.objects.filter(
            person=manager1.person
        )
        self.assertTrue(parcours_doctoral_predicates.is_part_of_doctoral_commission(manager1.person.user, request))

        self.predicate_context_patcher.target.context['role_qs'] = CddConfigurator.objects.filter(
            person=manager2.person
        )
        self.assertFalse(parcours_doctoral_predicates.is_part_of_doctoral_commission(manager2.person.user, request))

    def test_confirmation_paper_in_progress(self):
        parcours_doctoral = ParcoursDoctoralFactory()

        valid_status = [
            ChoixStatutParcoursDoctoral.ADMITTED.name,
            ChoixStatutParcoursDoctoral.SUBMITTED_CONFIRMATION.name,
            ChoixStatutParcoursDoctoral.CONFIRMATION_TO_BE_REPEATED.name,
        ]
        invalid_status = [
            ChoixStatutParcoursDoctoral.PASSED_CONFIRMATION.name,
            ChoixStatutParcoursDoctoral.NOT_ALLOWED_TO_CONTINUE.name,
        ]

        for status in valid_status:
            parcours_doctoral.status = status
            self.assertTrue(
                parcours_doctoral_predicates.confirmation_paper_in_progress(
                    parcours_doctoral.student.user, parcours_doctoral
                ),
                'This status must be accepted: {}'.format(status),
            )

        for status in invalid_status:
            parcours_doctoral.status = status
            self.assertFalse(
                parcours_doctoral_predicates.confirmation_paper_in_progress(
                    parcours_doctoral.student.user, parcours_doctoral
                ),
                'This status must not be accepted: {}'.format(status),
            )
