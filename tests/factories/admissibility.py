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

import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyDate

from parcours_doctoral.models.admissibility import Admissibility
from parcours_doctoral.tests.factories import PdfUploadFactory


class AdmissibilityFactory(DjangoModelFactory):
    class Meta:
        model = Admissibility

    decision_date = FuzzyDate(start_date=datetime.date(2020, 1, 1))
    manuscript_submission_date = FuzzyDate(start_date=datetime.date(2020, 1, 1))
    thesis_exam_board_opinion = factory.LazyAttribute(lambda _: [PdfUploadFactory().uuid])
    minutes = factory.LazyAttribute(lambda _: [PdfUploadFactory().uuid])
    minutes_canvas = factory.LazyAttribute(lambda _: [PdfUploadFactory().uuid])
    current_parcours_doctoral = factory.SelfAttribute('parcours_doctoral')
