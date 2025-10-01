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
import random

import factory

from deliberation.models.enums.numero_session import Session
from parcours_doctoral.ddd.formation.domain.model.enums import (
    StatutInscriptionEvaluation,
)
from parcours_doctoral.models import AssessmentEnrollment
from parcours_doctoral.tests.factories.activity import (
    UclCourseFactory,
    UclCourseWithClassFactory,
)


class AssessmentEnrollmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AssessmentEnrollment

    session = Session.JANUARY.name
    status = StatutInscriptionEvaluation.ACCEPTEE.name
    late_enrollment = False
    late_unenrollment = False
    course = factory.SubFactory(UclCourseFactory)
    submitted_mark = factory.LazyAttribute(lambda x: str(random.randrange(10, 20)))
    corrected_mark = factory.LazyAttribute(lambda x: str(random.randrange(10, 20)))


class AssessmentEnrollmentForClassFactory(AssessmentEnrollmentFactory):
    course = factory.SubFactory(UclCourseWithClassFactory)
