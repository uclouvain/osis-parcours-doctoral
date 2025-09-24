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
from django.conf import settings
from django.utils import translation

from base.models.enums.person_address_type import PersonAddressType
from base.models.person_address import PersonAddress
from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.commands import RecupererParcoursDoctoralQuery
from parcours_doctoral.ddd.dtos import ParcoursDoctoralDTO
from parcours_doctoral.exports.utils import parcours_doctoral_generate_pdf
from parcours_doctoral.models import Activity, ConfirmationPaper, ParcoursDoctoralTask
from parcours_doctoral.utils.formatting import format_address
from reference.services.mandates import (
    MandateFunctionEnum,
    MandatesException,
    MandatesService,
)


def confirmation_success_attestation(task_uuid, language=None):
    doctorate_task = ParcoursDoctoralTask.objects.select_related('task', 'parcours_doctoral__student').get(
        task__uuid=task_uuid
    )

    current_language = language or doctorate_task.parcours_doctoral.student.language

    with translation.override(current_language):
        # Load additional data
        doctorate_dto: ParcoursDoctoralDTO = message_bus_instance.invoke(
            RecupererParcoursDoctoralQuery(
                parcours_doctoral_uuid=doctorate_task.parcours_doctoral.uuid,
            )
        )

        confirmation_paper = ConfirmationPaper.objects.filter(
            parcours_doctoral=doctorate_task.parcours_doctoral,
            is_active=True,
        ).first()

        doctoral_training_ects_nb = Activity.objects.get_doctoral_training_credits_number(
            parcours_doctoral_uuid=doctorate_dto.uuid,
        )

        addresses = (
            PersonAddress.objects.filter(person=doctorate_task.parcours_doctoral.student)
            .select_related('country')
            .only('street', 'street_number', 'postal_code', 'city', 'country__name', 'country__name_en')
        )

        if addresses:
            contact_address = (
                addresses.filter(label=PersonAddressType.CONTACT.name).first()
                or addresses.filter(label=PersonAddressType.RESIDENTIAL.name).first()
                or addresses[0]
            )

            contact_address = format_address(
                street=contact_address.street,
                street_number=contact_address.street_number,
                postal_code=contact_address.postal_code,
                city=contact_address.city,
                country=getattr(
                    contact_address.country,
                    'name' if current_language == settings.LANGUAGE_CODE else 'name_en',
                ),
            )

        else:
            contact_address = ''

        cdd_president = []
        if settings.ESB_API_URL:
            try:
                cdd_president = MandatesService.get(
                    function=MandateFunctionEnum.PRESI,
                    entity_acronym=doctorate_dto.formation.entite_gestion.sigle,
                )
            except MandatesException:
                pass

        # Generate the pdf
        save_token = parcours_doctoral_generate_pdf(
            template='parcours_doctoral/exports/confirmation_success_attestation.html',
            filename='confirmation_attestation.pdf',
            context={
                'contact_address': contact_address,
                'cdd_president': cdd_president[0] if cdd_president else {},
                'confirmation_paper': confirmation_paper,
                'doctoral_training_ects_nb': doctoral_training_ects_nb,
                'parcours_doctoral': doctorate_dto,
            },
        )

        # Attach the file to the object
        confirmation_paper.certificate_of_achievement = [save_token]
        confirmation_paper.save()
