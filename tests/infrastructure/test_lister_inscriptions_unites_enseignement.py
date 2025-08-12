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
from django.test import TestCase

from base.tests import QueriesAssertionsMixin
from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.formation.commands import (
    ListerInscriptionsUnitesEnseignementQuery,
)
from parcours_doctoral.ddd.formation.domain.model.enums import StatutActivite
from parcours_doctoral.ddd.formation.dtos.inscription_unite_enseignement import (
    InscriptionUniteEnseignementDTO,
)
from parcours_doctoral.tests.factories.activity import UclCourseFactory


class ListerInscriptionsUnitesEnseignementTestCase(QueriesAssertionsMixin, TestCase):
    def test_list_with_no_activity(self):
        with self.assertNumQueriesLessThan(2):
            activities = message_bus_instance.invoke(
                ListerInscriptionsUnitesEnseignementQuery(
                    annee=2020,
                    code_unite_enseignement='UE1',
                )
            )

        self.assertEqual(len(activities), 0)

    def test_list_with_activities(self):
        first_course = UclCourseFactory(
            learning_unit_year__academic_year__year=2020,
            learning_unit_year__acronym='UE1',
            status=StatutActivite.ACCEPTEE.name,
        )
        second_course = UclCourseFactory(
            learning_unit_year__academic_year__year=2020,
            learning_unit_year__acronym='UE1',
            status=StatutActivite.ACCEPTEE.name,
        )
        other_status_course = UclCourseFactory(
            learning_unit_year__academic_year__year=2020,
            learning_unit_year__acronym='UE1',
            status=StatutActivite.SOUMISE.name,
        )
        other_year_course = UclCourseFactory(
            learning_unit_year__academic_year__year=2019,
            learning_unit_year__acronym='UE1',
            status=StatutActivite.SOUMISE.name,
        )
        other_learning_unit_acronym_course = UclCourseFactory(
            learning_unit_year__academic_year__year=2020,
            learning_unit_year__acronym='UE2',
            status=StatutActivite.SOUMISE.name,
        )

        with self.assertNumQueriesLessThan(3, verbose=True):
            activities = message_bus_instance.invoke(
                ListerInscriptionsUnitesEnseignementQuery(
                    annee=2020,
                    code_unite_enseignement='UE1',
                )
            )

        self.assertCountEqual(
            activities,
            [
                InscriptionUniteEnseignementDTO(
                    noma=first_course.parcours_doctoral.student.student_set.first().registration_id,
                    annee=2020,
                    sigle_formation=first_course.parcours_doctoral.training.acronym,
                    code_unite_enseignement='UE1',
                ),
                InscriptionUniteEnseignementDTO(
                    noma=second_course.parcours_doctoral.student.student_set.first().registration_id,
                    annee=2020,
                    sigle_formation=second_course.parcours_doctoral.training.acronym,
                    code_unite_enseignement='UE1',
                ),
            ],
        )
