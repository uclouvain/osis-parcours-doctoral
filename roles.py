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
from rules import always_allow

from osis_role import role
from parcours_doctoral.auth.predicates.parcours_doctoral import (
    complementary_training_enabled,
    has_valid_enrollment,
    is_jury_approuve_ca,
    is_jury_in_progress,
    is_jury_signing_in_progress,
    is_part_of_education_group,
    is_related_to_an_admission,
    private_defense_is_authorised,
    private_defense_is_submitted,
    public_defense_is_authorised,
    public_defense_is_submitted,
    submitted_confirmation_paper,
)
from parcours_doctoral.auth.roles.adre_manager import AdreManager
from parcours_doctoral.auth.roles.adre_secretary import AdreSecretary
from parcours_doctoral.auth.roles.auditor import Auditor
from parcours_doctoral.auth.roles.ca_member import CommitteeMember
from parcours_doctoral.auth.roles.cdd_configurator import CddConfigurator
from parcours_doctoral.auth.roles.das import SectorAdministrativeDirector
from parcours_doctoral.auth.roles.jury_member import JuryMember
from parcours_doctoral.auth.roles.jury_secretary import JurySecretary
from parcours_doctoral.auth.roles.promoter import Promoter
from parcours_doctoral.auth.roles.sceb_manager import ScebManager
from parcours_doctoral.auth.roles.student import Student

role.role_manager.register(CddConfigurator)
role.role_manager.register(JurySecretary)
role.role_manager.register(AdreSecretary)
role.role_manager.register(AdreManager)
role.role_manager.register(Student)
role.role_manager.register(Promoter)
role.role_manager.register(CommitteeMember)
role.role_manager.register(Auditor)
role.role_manager.register(SectorAdministrativeDirector)
role.role_manager.register(JuryMember)
role.role_manager.register(ScebManager)


PROGRAM_MANAGER_RULES = {
    # Doctorats
    'parcours_doctoral.view_parcours_doctoral_home': always_allow,
    'parcours_doctoral.view_parcours_doctoral': always_allow,
    'parcours_doctoral.view_historyentry': is_part_of_education_group,
    'parcours_doctoral.view_person': is_part_of_education_group,
    'parcours_doctoral.view_coordinates': is_part_of_education_group,
    'parcours_doctoral.view_secondary_studies': is_part_of_education_group,
    'parcours_doctoral.view_curriculum': is_part_of_education_group,
    'parcours_doctoral.view_languages': is_part_of_education_group,
    'parcours_doctoral.view_internalnote': is_part_of_education_group,
    # --- Projet de recherche
    'parcours_doctoral.view_project': is_part_of_education_group,
    'parcours_doctoral.change_project': is_part_of_education_group & has_valid_enrollment,
    'parcours_doctoral.view_funding': is_part_of_education_group,
    'parcours_doctoral.change_funding': is_part_of_education_group & has_valid_enrollment,
    'parcours_doctoral.view_cotutelle': is_related_to_an_admission & is_part_of_education_group,
    'parcours_doctoral.change_cotutelle': is_related_to_an_admission
    & is_part_of_education_group
    & has_valid_enrollment,
    'parcours_doctoral.view_supervision': is_part_of_education_group,
    'parcours_doctoral.add_supervision_member': is_part_of_education_group & has_valid_enrollment,
    'parcours_doctoral.edit_external_supervision_member': is_part_of_education_group & has_valid_enrollment,
    'parcours_doctoral.remove_supervision_member': is_part_of_education_group & has_valid_enrollment,
    'parcours_doctoral.approve_member_by_pdf': is_part_of_education_group & has_valid_enrollment,
    # --- Documents
    'parcours_doctoral.view_documents': is_part_of_education_group,
    'parcours_doctoral.change_documents': is_part_of_education_group & has_valid_enrollment,
    # --- Confirmation
    'parcours_doctoral.view_confirmation': is_related_to_an_admission & is_part_of_education_group,
    'parcours_doctoral.change_confirmation': is_related_to_an_admission
    & is_part_of_education_group
    & has_valid_enrollment,
    'parcours_doctoral.change_confirmation_extension': is_related_to_an_admission
    & is_part_of_education_group
    & has_valid_enrollment,
    'parcours_doctoral.make_confirmation_decision': is_related_to_an_admission
    & is_part_of_education_group
    & submitted_confirmation_paper
    & has_valid_enrollment,
    'parcours_doctoral.upload_pdf_confirmation': is_related_to_an_admission
    & is_part_of_education_group
    & has_valid_enrollment,
    # -- Formation doctorale
    'parcours_doctoral.view_training': is_part_of_education_group,
    'parcours_doctoral.view_doctoral_training': is_part_of_education_group,
    'parcours_doctoral.view_complementary_training': is_part_of_education_group & complementary_training_enabled,
    'parcours_doctoral.view_course_enrollment': is_part_of_education_group,
    'parcours_doctoral.view_assessment_enrollment': is_part_of_education_group,
    'parcours_doctoral.change_assessment_enrollment': is_part_of_education_group & has_valid_enrollment,
    'parcours_doctoral.change_activity': is_part_of_education_group & has_valid_enrollment,
    'parcours_doctoral.delete_activity': is_part_of_education_group & has_valid_enrollment,
    'parcours_doctoral.refuse_activity': is_part_of_education_group & has_valid_enrollment,
    'parcours_doctoral.restore_activity': is_part_of_education_group & has_valid_enrollment,
    # -- Jury
    'parcours_doctoral.view_jury': is_part_of_education_group,
    'parcours_doctoral.change_jury': is_part_of_education_group & has_valid_enrollment,
    'parcours_doctoral.jury_request_signatures': is_part_of_education_group
    & is_jury_in_progress
    & has_valid_enrollment,
    'parcours_doctoral.jury_reset_signatures': is_part_of_education_group
    & is_jury_signing_in_progress
    & has_valid_enrollment,
    'parcours_doctoral.approve_jury': is_part_of_education_group & is_jury_approuve_ca & has_valid_enrollment,
    # -- Défense
    'parcours_doctoral.view_private_defense': is_part_of_education_group,
    'parcours_doctoral.authorise_private_defense': is_part_of_education_group
    & has_valid_enrollment
    & private_defense_is_submitted,
    'parcours_doctoral.invite_jury_to_private_defense': is_part_of_education_group
    & has_valid_enrollment
    & private_defense_is_authorised,
    'parcours_doctoral.make_private_defense_decision': is_part_of_education_group
    & has_valid_enrollment
    & private_defense_is_authorised,
    'parcours_doctoral.change_private_defense': is_part_of_education_group & has_valid_enrollment,
    # -- Soutenance
    'parcours_doctoral.view_public_defense': is_part_of_education_group,
    'parcours_doctoral.invite_jury_to_public_defense': is_part_of_education_group
    & has_valid_enrollment
    & public_defense_is_submitted,
    'parcours_doctoral.authorise_public_defense': is_part_of_education_group
    & has_valid_enrollment
    & public_defense_is_submitted,
    'parcours_doctoral.make_public_defense_decision': is_part_of_education_group
    & has_valid_enrollment
    & public_defense_is_authorised,
    # -- Commentaire
    'parcours_doctoral.view_comments': is_part_of_education_group,
    'parcours_doctoral.change_comments': is_part_of_education_group,
    # -- Messages
    'parcours_doctoral.send_message': is_part_of_education_group,
}
