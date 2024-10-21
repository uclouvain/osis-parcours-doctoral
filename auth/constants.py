# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
    'coordonnees': 'parcours_doctoral.view_parcours_doctoral_coordinates',
    'cotutelle': 'parcours_doctoral.view_parcours_doctoral_cotutelle',
    'person': 'parcours_doctoral.view_parcours_doctoral_person',
    # Training choice
    'training-choice': 'parcours_doctoral.view_parcours_doctoral_training_choice',
    # Previous experience
    'curriculum': 'parcours_doctoral.view_parcours_doctoral_curriculum',
    'educational': '',
    'educational_create': '',
    'non_educational': '',
    'non_educational_create': '',
    'education': 'parcours_doctoral.view_parcours_doctoral_secondary_studies',
    'languages': 'parcours_doctoral.view_parcours_doctoral_languages',
    # Project
    'project': 'parcours_doctoral.view_parcours_doctoral_project',
    'supervision': 'parcours_doctoral.view_parcours_doctoral_supervision',
    # Confirmation exam
    'confirmation': 'parcours_doctoral.view_parcours_doctoral_confirmation',
    'extension-request': 'parcours_doctoral.view_parcours_doctoral_confirmation',
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
    # Jury
    'jury-preparation': 'parcours_doctoral.view_parcours_doctoral_jury',
    'jury': 'parcours_doctoral.view_parcours_doctoral_jury',
    # Management
    'internal-note': 'parcours_doctoral.view_internalnote',
    'debug': 'parcours_doctoral.view_debug_info',
    'comments': 'parcours_doctoral.view_enrolment_application',
    'checklist': 'parcours_doctoral.view_checklist',
    # Documents
    'documents': 'parcours_doctoral.view_documents_management',
}

# Association between a write-only tab name (path name) and a permission
UPDATE_ACTIONS_BY_TAB = {
    # Personal data
    'coordonnees': 'parcours_doctoral.change_parcours_doctoral_coordinates',
    'cotutelle': 'parcours_doctoral.change_parcours_doctoral_cotutelle',
    'person': 'parcours_doctoral.change_parcours_doctoral_person',
    # Training choice
    'training-choice': 'parcours_doctoral.change_parcours_doctoral_training_choice',
    # Previous experience
    'curriculum': 'parcours_doctoral.change_parcours_doctoral_curriculum',
    'educational': '',
    'educational_create': '',
    'non_educational': '',
    'non_educational_create': '',
    'education': 'parcours_doctoral.change_parcours_doctoral_secondary_studies',
    'languages': 'parcours_doctoral.change_parcours_doctoral_languages',
    # Project
    'project': 'parcours_doctoral.change_parcours_doctoral_project',
    'supervision': 'parcours_doctoral.change_parcours_doctoral_supervision',
    # Confirmation exam
    'confirmation': 'parcours_doctoral.change_parcours_doctoral_confirmation',
    'extension-request': 'parcours_doctoral.change_parcours_doctoral_confirmation_extension',
    # Mails
    'send-mail': 'parcours_doctoral.send_message',
    # Training
    'training': '',
    'doctoral-training': '',
    'complementary-training': '',
    'course-enrollment': '',
    # Management
    'documents': 'parcours_doctoral.view_documents_management',
    'checklist': 'parcours_doctoral.view_checklist',
    # Jury
    'jury-preparation': 'parcours_doctoral.change_parcours_doctoral_jury',
    'jury': 'parcours_doctoral.change_parcours_doctoral_jury',
}
