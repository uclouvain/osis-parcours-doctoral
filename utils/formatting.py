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
from django.template.defaultfilters import floatformat


def format_address(street: str, street_number: str, postal_code: str, city: str, country: str):
    """
    Return the concatenation of the street, street number, postal code, city and state of an address.
    :param street: The street name
    :param street_number: The street number
    :param postal_code: The postal code
    :param city: The city
    :param country: The country
    :return: The concatenated address
    """
    address_parts = [
        '{street} {street_number}'.format(street=street, street_number=street_number).strip(),
        '{postal_code} {city}'.format(postal_code=postal_code, city=city).strip(),
        country,
    ]
    return ', '.join(filter(lambda part: part and len(part) > 1, address_parts))


def format_activity_ects(ects):
    """Format the number of ECTS related to an activity to display them."""
    if not ects:
        ects = ''
    ects = floatformat(ects, -2)
    return f'{ects} ECTS'
