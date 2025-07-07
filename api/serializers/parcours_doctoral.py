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
from rest_framework import serializers

from backoffice.settings.rest_framework.fields import ActionLinksField
from base.utils.serializers import DTOSerializer
from parcours_doctoral.api.serializers.fields import PARCOURS_DOCTORAL_ACTION_LINKS
from parcours_doctoral.ddd.dtos import ParcoursDoctoralDTO
from parcours_doctoral.ddd.dtos.parcours_doctoral import (
    ParcoursDoctoralRechercheEtudiantDTO,
)


class ParcoursDoctoralIdentityDTOSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(read_only=True)


class ParcoursDoctoralDTOSerializer(DTOSerializer):
    links = ActionLinksField(
        actions={
            key: PARCOURS_DOCTORAL_ACTION_LINKS[key]
            for key in [
                # Project
                'retrieve_project',
                # Cotutelle
                'retrieve_cotutelle',
                'update_cotutelle',
                # Funding
                'retrieve_funding',
                'update_funding',
                # Supervision
                'retrieve_supervision',
                'retrieve_supervision_canvas',
                # Confirmation
                'retrieve_confirmation',
                'update_confirmation',
                'update_confirmation_extension',
                # Training
                'retrieve_doctorate_training',
                'retrieve_complementary_training',
                'retrieve_course_enrollment',
                'retrieve_assessment_enrollment',
                'add_training',
                'submit_training',
                'assent_training',
                # Jury
                'retrieve_jury_preparation',
                'update_jury_preparation',
                'list_jury_members',
                'create_jury_members',
                'jury_request_signatures',
                'jury_add_approval',
                'jury_approve_by_pdf',
            ]
        }
    )

    class Meta:
        source = ParcoursDoctoralDTO


class ParcoursDoctoralRechercheDTOSerializer(DTOSerializer):
    links = ActionLinksField(
        actions={
            **{
                action: PARCOURS_DOCTORAL_ACTION_LINKS[action]
                for action in [
                    # Project
                    'retrieve_project',
                    # Funding
                    'retrieve_funding',
                    'update_funding',
                    # Cotutelle
                    'retrieve_cotutelle',
                    'update_cotutelle',
                    # Supervision
                    'retrieve_supervision',
                    'retrieve_supervision_canvas',
                    # Confirmation
                    'retrieve_confirmation',
                    'update_confirmation',
                    'update_confirmation_extension',
                    # Training
                    'retrieve_doctorate_training',
                    'retrieve_complementary_training',
                    'retrieve_course_enrollment',
                    'add_training',
                    'submit_training',
                    'assent_training',
                    # Jury
                    'retrieve_jury_preparation',
                    'update_jury_preparation',
                    'list_jury_members',
                    'create_jury_members',
                ]
            },
        }
    )

    class Meta:
        source = ParcoursDoctoralRechercheEtudiantDTO
