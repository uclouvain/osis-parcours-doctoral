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
from django.conf import settings
from django.utils.translation import get_language

from base.forms.utils import EMPTY_CHOICE
from reference.models.country import Country


def get_country_initial_choices(iso_code):
    if not iso_code:
        return EMPTY_CHOICE
    try:
        country = Country.objects.get(iso_code=iso_code)
    except Country.DoesNotExist:
        return EMPTY_CHOICE
    return EMPTY_CHOICE + (
        (country.iso_code, country.name if get_language() == settings.LANGUAGE_CODE_FR else country.name_en),
    )
