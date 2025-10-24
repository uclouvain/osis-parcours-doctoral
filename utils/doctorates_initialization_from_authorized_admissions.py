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
import logging

from django.conf import settings
from django.db import models
from django.db.models import Value

from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.commands import InitialiserParcoursDoctoralCommand

logger = logging.getLogger(settings.DEFAULT_LOGGER)


def initialize_the_doctorates_from_authorized_admissions(doctorate_admission_model, on_migration=False):
    """
    Initialize the doctorates related to the admissions in the 'Application accepted' status.

    :param on_migration: Set it to true if this method is used in the migration.
    :param doctorate_admission_model: The doctorate admission model class.
    :return: A tuple of two lists of the processed admissions references: the first one for the admissions whose
    the process hasn't encountered an error and the second one whose the process has encountered an error.
    :rtype: tuple[list[int], list[int]]
    """
    qs = doctorate_admission_model.objects.filter(
        status=ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name,
        parcoursdoctoral__isnull=True,
    )

    if on_migration:
        qs = qs.annotate(
            proposition_uuid=models.F('baseadmission_ptr__uuid'),
            proposition_reference=models.F('baseadmission_ptr__reference'),
            created_at=Value(''),  # Otherwise, the field is not found (FieldDoesNotExist exception)
        )
    else:
        qs = qs.annotate(
            proposition_uuid=models.F('uuid'),
            proposition_reference=models.F('reference'),
        )

    qs = qs.values('proposition_uuid', 'proposition_reference')

    valid_references = []
    invalid_references = []

    for admission in qs:
        try:
            message_bus_instance.invoke(
                InitialiserParcoursDoctoralCommand(proposition_uuid=admission['proposition_uuid']),
            )
            valid_references.append(admission['proposition_reference'])
        except Exception:
            invalid_references.append(admission['proposition_reference'])

    error_message = (
        f' Some errors have been encountered for the following admission(s): '
        f'{", ".join(map(str, invalid_references))}.'
        if invalid_references
        else ''
    )

    logger.info(
        msg=(
            f'[PARCOURS_DOCTORAL] Initialize the doctorate(s) for {len(valid_references)}/{len(qs)} '
            f'admission(s).{error_message}'
        )
    )

    return valid_references, invalid_references
