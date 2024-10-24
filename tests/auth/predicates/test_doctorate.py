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

from django.test import TestCase

from admission.tests.factories import DoctorateAdmissionFactory
from parcours_doctoral.auth.predicates import parcours_doctoral
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral


class PredicatesTestCase(TestCase):
    def setUp(self):
        self.predicate_context_patcher = mock.patch(
            "rules.Predicate.context",
            new_callable=mock.PropertyMock,
            return_value={'perm_name': 'dummy-perm'},
        )
        self.predicate_context_patcher.start()
        self.addCleanup(self.predicate_context_patcher.stop)

    def test_confirmation_paper_in_progress(self):
        admission = DoctorateAdmissionFactory()

        valid_status = [
            ChoixStatutParcoursDoctoral.ADMITTED.name,
            ChoixStatutParcoursDoctoral.SUBMITTED_CONFIRMATION.name,
            ChoixStatutParcoursDoctoral.CONFIRMATION_TO_BE_REPEATED.name,
        ]
        invalid_status = [
            ChoixStatutParcoursDoctoral.ADMISSION_IN_PROGRESS.name,
            ChoixStatutParcoursDoctoral.PASSED_CONFIRMATION.name,
            ChoixStatutParcoursDoctoral.NOT_ALLOWED_TO_CONTINUE.name,
        ]

        for status in valid_status:
            admission.post_enrolment_status = status
            self.assertTrue(
                parcours_doctoral.confirmation_paper_in_progress(admission.candidate.user, admission),
                'This status must be accepted: {}'.format(status),
            )

        for status in invalid_status:
            admission.post_enrolment_status = status
            self.assertFalse(
                parcours_doctoral.confirmation_paper_in_progress(admission.candidate.user, admission),
                'This status must not be accepted: {}'.format(status),
            )
