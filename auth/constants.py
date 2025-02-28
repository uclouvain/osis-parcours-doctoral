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

# Association between a read-only tab name (path name) and a permission
READ_ACTIONS_BY_TAB = {
    # Personal data
    'coordonnees': 'parcours_doctoral.view_coordinates',
    'cotutelle': 'parcours_doctoral.view_cotutelle',
    'person': 'parcours_doctoral.view_person',
    # Training choice
    'training-choice': 'parcours_doctoral.view_training_choice',
    # Previous experience
    'curriculum': 'parcours_doctoral.view_curriculum',
    'educational': '',
    'educational_create': '',
    'non_educational': '',
    'non_educational_create': '',
    'education': 'parcours_doctoral.view_secondary_studies',
    'languages': 'parcours_doctoral.view_languages',
    # Project
    'project': 'parcours_doctoral.view_project',
    'funding': 'parcours_doctoral.view_funding',
    'supervision': 'parcours_doctoral.view_supervision',
    # Confirmation exam
    'confirmation': 'parcours_doctoral.view_confirmation',
    'extension-request': 'parcours_doctoral.view_confirmation',
    'extension-request-opinion': 'parcours_doctoral.view_confirmation',
    # History
    'history': 'parcours_doctoral.view_historyentry',
    'history-all': 'parcours_doctoral.view_historyentry',
    # Mails
    'send-mail': 'parcours_doctoral.send_message',
    # Training
    'training': 'parcours_doctoral.view_training',
    'doctoral-training': 'parcours_doctoral.view_doctoral_training',
    'complementary-training': 'parcours_doctoral.view_complementary_training',
    'course-enrollment': 'parcours_doctoral.view_course_enrollment',
    'assessment-enrollment': 'parcours_doctoral.view_assessment_enrollment',
    # Jury
    'jury-preparation': 'parcours_doctoral.view_jury',
    'jury': 'parcours_doctoral.view_jury',
    # Management
    'internal-note': 'parcours_doctoral.view_internalnote',
    'debug': 'parcours_doctoral.view_debug_info',
    'comments': 'parcours_doctoral.view_comments',
    'checklist': 'parcours_doctoral.view_checklist',
    # Documents
    'documents': 'parcours_doctoral.view_documents',
}

# Association between a write-only tab name (path name) and a permission
UPDATE_ACTIONS_BY_TAB = {
    # Personal data
    'coordonnees': 'parcours_doctoral.change_coordinates',
    'cotutelle': 'parcours_doctoral.change_cotutelle',
    'person': 'parcours_doctoral.change_person',
    # Training choice
    'training-choice': 'parcours_doctoral.change_training_choice',
    # Previous experience
    'curriculum': 'parcours_doctoral.change_curriculum',
    'educational': '',
    'educational_create': '',
    'non_educational': '',
    'non_educational_create': '',
    'education': 'parcours_doctoral.change_secondary_studies',
    'languages': 'parcours_doctoral.change_languages',
    # Project
    'project': 'parcours_doctoral.change_project',
    'funding': 'parcours_doctoral.change_funding',
    'supervision': 'parcours_doctoral.change_supervision',
    # Confirmation exam
    'confirmation': 'parcours_doctoral.change_confirmation',
    'extension-request': 'parcours_doctoral.change_confirmation_extension',
    'extension-request-opinion': 'parcours_doctoral.change_confirmation_extension',
    # Mails
    'send-mail': 'parcours_doctoral.send_message',
    # Training
    'training': '',
    'doctoral-training': '',
    'complementary-training': '',
    'course-enrollment': '',
    'assessment-enrollment': 'parcours_doctoral.change_assessment_enrollment',
    # Management
    'documents': 'parcours_doctoral.view_documents',
    'checklist': 'parcours_doctoral.view_checklist',
    'comments': 'parcours_doctoral.change_comments',
    # Jury
    'jury-preparation': 'parcours_doctoral.change_jury',
    'jury': 'parcours_doctoral.change_jury',
}
