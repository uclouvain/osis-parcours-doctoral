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
from rest_framework import serializers

from base.models.entity_version import EntityVersion
from base.models.enums.entity_type import EntityType

PARCOURS_DOCTORAL_ACTION_LINKS = {
    # Lists
    'list': {
        'path_name': 'parcours_doctoral_api_v1:list',
        'method': 'GET',
    },
    'supervised_list': {
        'path_name': 'parcours_doctoral_api_v1:supervised_list',
        'method': 'GET',
    },
    # Project tabs
    'retrieve_project': {
        'path_name': 'parcours_doctoral_api_v1:project',
        'method': 'GET',
        'params': ['uuid'],
    },
    'retrieve_funding': {
        'path_name': 'parcours_doctoral_api_v1:funding',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_funding': {
        'path_name': 'parcours_doctoral_api_v1:funding',
        'method': 'PUT',
        'params': ['uuid'],
    },
    'retrieve_cotutelle': {
        'path_name': 'parcours_doctoral_api_v1:cotutelle',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_cotutelle': {
        'path_name': 'parcours_doctoral_api_v1:cotutelle',
        'method': 'PUT',
        'params': ['uuid'],
    },
    # Supervision group
    'retrieve_supervision': {
        'path_name': 'parcours_doctoral_api_v1:supervision',
        'method': 'GET',
        'params': ['uuid'],
    },
    'retrieve_supervision_canvas': {
        'path_name': 'parcours_doctoral_api_v1:supervision_canvas',
        'method': 'GET',
        'params': ['uuid'],
    },
    # Confirmation exam
    'retrieve_confirmation': {
        'path_name': 'parcours_doctoral_api_v1:confirmation',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_confirmation': {
        'path_name': 'parcours_doctoral_api_v1:last_confirmation',
        'method': 'PUT',
        'params': ['uuid'],
    },
    'update_confirmation_extension': {
        'path_name': 'parcours_doctoral_api_v1:last_confirmation',
        'method': 'POST',
        'params': ['uuid'],
    },
    'upload_pdf_confirmation': {
        'path_name': 'parcours_doctoral_api_v1:supervised_confirmation',
        'method': 'PUT',
        'params': ['uuid'],
    },
    # Training
    'add_training': {
        'path_name': 'parcours_doctoral_api_v1:doctoral-training',
        'method': 'POST',
        'params': ['uuid'],
    },
    'assent_training': {
        'path_name': 'parcours_doctoral_api_v1:training-assent',
        'method': 'POST',
        'params': ['uuid'],
    },
    'submit_training': {
        'path_name': 'parcours_doctoral_api_v1:training-submit',
        'method': 'POST',
        'params': ['uuid'],
    },
    'retrieve_doctorate_training': {
        'path_name': 'parcours_doctoral_api_v1:doctoral-training',
        'method': 'GET',
        'params': ['uuid'],
    },
    'retrieve_complementary_training': {
        'path_name': 'parcours_doctoral_api_v1:complementary-training',
        'method': 'GET',
        'params': ['uuid'],
    },
    'retrieve_course_enrollment': {
        'path_name': 'parcours_doctoral_api_v1:course-enrollment',
        'method': 'GET',
        'params': ['uuid'],
    },
    'retrieve_assessment_enrollment': {
        'path_name': 'parcours_doctoral_api_v1:assessment-enrollment-list',
        'method': 'GET',
        'params': ['uuid'],
    },
    # Jury
    'retrieve_jury_preparation': {
        'path_name': 'parcours_doctoral_api_v1:jury-preparation',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_jury_preparation': {
        'path_name': 'parcours_doctoral_api_v1:jury-preparation',
        'method': 'POST',
        'params': ['uuid'],
    },
    'list_jury_members': {
        'path_name': 'parcours_doctoral_api_v1:jury-members-list',
        'method': 'GET',
        'params': ['uuid'],
    },
    'create_jury_members': {
        'path_name': 'parcours_doctoral_api_v1:jury-members-list',
        'method': 'POST',
        'params': ['uuid'],
    },
    'jury_add_approval': {
        'path_name': 'parcours_doctoral_api_v1:jury-approvals',
        'method': 'POST',
        'params': ['uuid'],
    },
    'jury_request_signatures': {
        'path_name': 'parcours_doctoral_api_v1:jury-request-signatures',
        'method': 'POST',
        'params': ['uuid'],
    },
    'jury_approve_by_pdf': {
        'path_name': 'parcours_doctoral_api_v1:jury-approve-by-pdf',
        'method': 'POST',
        'params': ['uuid'],
    },
    # Admissibility
    'retrieve_admissibility_minutes_canvas': {
        'path_name': 'parcours_doctoral_api_v1:admissibility-minutes',
        'method': 'GET',
        'params': ['uuid'],
    },
    'submit_admissibility_minutes_and_opinions': {
        'path_name': 'parcours_doctoral_api_v1:admissibility-minutes',
        'method': 'PUT',
        'params': ['uuid'],
    },
    # Admissibility
    'retrieve_admissibility': {
        'path_name': 'parcours_doctoral_api_v1:admissibility-list',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_admissibility': {
        'path_name': 'parcours_doctoral_api_v1:admissibility-list',
        'method': 'PUT',
        'params': ['uuid'],
    },
    # Private defense
    'retrieve_private_defense': {
        'path_name': 'parcours_doctoral_api_v1:private-defense-list',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_private_defense': {
        'path_name': 'parcours_doctoral_api_v1:private-defense-list',
        'method': 'PUT',
        'params': ['uuid'],
    },
    'retrieve_private_defense_minutes_canvas': {
        'path_name': 'parcours_doctoral_api_v1:private-defense-minutes',
        'method': 'GET',
        'params': ['uuid'],
    },
    'submit_private_defense_minutes': {
        'path_name': 'parcours_doctoral_api_v1:private-defense-minutes',
        'method': 'PUT',
        'params': ['uuid'],
    },
    # Authorization distribution
    'retrieve_authorization_distribution': {
        'path_name': 'parcours_doctoral_api_v1:authorization-distribution',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_authorization_distribution': {
        'path_name': 'parcours_doctoral_api_v1:authorization-distribution',
        'method': 'PUT',
        'params': ['uuid'],
    },
    # Manuscript validation
    'validate_manuscript': {
        'path_name': 'parcours_doctoral_api_v1:manuscript-validation',
        'method': 'PUT',
        'params': ['uuid'],
    },
    # Public defense
    'retrieve_public_defense': {
        'path_name': 'parcours_doctoral_api_v1:public-defense',
        'method': 'GET',
        'params': ['uuid'],
    },
    'update_public_defense': {
        'path_name': 'parcours_doctoral_api_v1:public-defense',
        'method': 'PUT',
        'params': ['uuid'],
    },
    'retrieve_public_defense_minutes_canvas': {
        'path_name': 'parcours_doctoral_api_v1:public-defense-minutes',
        'method': 'GET',
        'params': ['uuid'],
    },
    'submit_public_defense_minutes': {
        'path_name': 'parcours_doctoral_api_v1:public-defense-minutes',
        'method': 'PUT',
        'params': ['uuid'],
    },
}


class RelatedInstituteField(serializers.CharField, serializers.SlugRelatedField):
    def __init__(self, **kwargs):
        kwargs.setdefault('slug_field', 'uuid')
        kwargs.setdefault('queryset', EntityVersion.objects.filter(entity_type=EntityType.INSTITUTE.name))
        kwargs.setdefault('allow_null', True)
        kwargs.setdefault('allow_blank', True)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        if data:
            return serializers.SlugRelatedField.to_internal_value(self, data)

    def to_representation(self, value):
        if value:
            return str(serializers.SlugRelatedField.to_representation(self, value))
