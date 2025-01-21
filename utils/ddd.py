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
from collections import defaultdict
from typing import Dict

from backoffice.settings.rest_framework.exception_handler import get_error_data
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from osis_common.ddd.interface import BusinessException, QueryRequest


def sort_business_exceptions(exception: BusinessException):
    return getattr(exception, 'status_code', ''), None


def gather_business_exceptions(command: QueryRequest) -> Dict[str, list]:
    from infrastructure.messages_bus import message_bus_instance

    data = defaultdict(list)
    try:
        # Trigger the verification command
        message_bus_instance.invoke(command)
    except MultipleBusinessExceptions as exc:
        # Gather all errors for output
        sorted_exceptions = sorted(exc.exceptions, key=sort_business_exceptions)

        for exception in sorted_exceptions:
            data = get_error_data(data, exception, {})

    return data
