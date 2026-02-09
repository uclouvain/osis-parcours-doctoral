# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

import freezegun
from django.test import TestCase

from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import (
    AcademicYear,
    AcademicYearIdentity,
)
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import (
    AcademicYearInMemoryRepository,
)
from parcours_doctoral.ddd.read_view.queries import ListerTousParcoursDoctorauxQuery
from parcours_doctoral.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from parcours_doctoral.infrastructure.parcours_doctoral.repository.in_memory.parcours_doctoral import (
    ParcoursDoctoralInMemoryRepository,
)


@freezegun.freeze_time('2023-01-01')
class TestListerTousParcoursDoctoral(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.academic_year_repository = AcademicYearInMemoryRepository()
        cls.academic_year_repository.save(
            AcademicYear(
                entity_id=AcademicYearIdentity(year=2022),
                start_date=datetime.date(2022, 9, 15),
                end_date=datetime.date(2022 + 1, 9, 30),
            )
        )

    def setUp(self) -> None:
        self.cmd = ListerTousParcoursDoctorauxQuery(matricule_doctorant='1')
        self.message_bus = message_bus_in_memory_instance
        ParcoursDoctoralInMemoryRepository.reset()

    def test_should_rechercher_par_matricule(self):
        propositions = self.message_bus.invoke(self.cmd)
        self.assertEqual(len(propositions), 12)
        for proposition in propositions:
            self.assertEqual(proposition.matricule_doctorant, '1')
