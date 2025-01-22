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

from parcours_doctoral.utils.formatting import format_address


class FormattingTestCase(TestCase):
    def test_format_address(self):
        self.assertEqual(
            format_address(
                street='rue de la paix',
                street_number='1',
                postal_code='1000',
                city='Bruxelles',
                country='Belgique',
            ),
            'rue de la paix 1, 1000 Bruxelles, Belgique',
        )

        self.assertEqual(
            format_address(
                street='rue de la paix',
                street_number='',
                postal_code='1000',
                city='Bruxelles',
                country='Belgique',
            ),
            'rue de la paix, 1000 Bruxelles, Belgique',
        )

        self.assertEqual(
            format_address(
                street='rue de la paix',
                street_number='1',
                postal_code='',
                city='Bruxelles',
                country='Belgique',
            ),
            'rue de la paix 1, Bruxelles, Belgique',
        )

        self.assertEqual(
            format_address(
                street='rue de la paix',
                street_number='',
                postal_code='',
                city='Bruxelles',
                country='Belgique',
            ),
            'rue de la paix, Bruxelles, Belgique',
        )

        self.assertEqual(
            format_address(
                street='',
                street_number='',
                postal_code='',
                city='Bruxelles',
                country='Belgique',
            ),
            'Bruxelles, Belgique',
        )

        self.assertEqual(
            format_address(
                street='',
                street_number='',
                postal_code='',
                city='',
                country='Belgique',
            ),
            'Belgique',
        )