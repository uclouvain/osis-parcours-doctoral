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
from rules import always_allow

from osis_role import role
from parcours_doctoral.auth.predicates.parcours_doctoral import (
    complementary_training_enabled,
    is_jury_in_progress,
    is_part_of_education_group,
    submitted_confirmation_paper,
)
from parcours_doctoral.auth.roles.adre import AdreSecretary
from parcours_doctoral.auth.roles.ca_member import CommitteeMember
from parcours_doctoral.auth.roles.cdd_configurator import CddConfigurator
from parcours_doctoral.auth.roles.jury_secretary import JurySecretary
from parcours_doctoral.auth.roles.promoter import Promoter
from parcours_doctoral.auth.roles.student import Student

role.role_manager.register(CddConfigurator)
role.role_manager.register(JurySecretary)
role.role_manager.register(AdreSecretary)
role.role_manager.register(Student)
role.role_manager.register(Promoter)
role.role_manager.register(CommitteeMember)


PROGRAM_MANAGER_RULES = {
    # Doctorats
    'parcours_doctoral.view_parcours_doctoral': always_allow,
    # --- Projet de recherche
    'parcours_doctoral.view_supervision': is_part_of_education_group,
    # --- Confirmation
    'parcours_doctoral.view_confirmation': is_part_of_education_group,
    'parcours_doctoral.change_confirmation': is_part_of_education_group,
    'parcours_doctoral.change_confirmation_extension': is_part_of_education_group,
    'parcours_doctoral.make_confirmation_decision': is_part_of_education_group & submitted_confirmation_paper,
    'parcours_doctoral.send_message': is_part_of_education_group,
    # -- Formation doctorale
    'parcours_doctoral.view_training': is_part_of_education_group,
    'parcours_doctoral.view_doctoral_training': is_part_of_education_group,
    'parcours_doctoral.view_complementary_training': is_part_of_education_group & complementary_training_enabled,
    'parcours_doctoral.view_course_enrollment': is_part_of_education_group,
    'parcours_doctoral.change_activity': is_part_of_education_group,
    'parcours_doctoral.delete_activity': is_part_of_education_group,
    'parcours_doctoral.refuse_activity': is_part_of_education_group,
    'parcours_doctoral.restore_activity': is_part_of_education_group,
    # -- Jury
    'parcours_doctoral.view_jury': is_part_of_education_group & is_jury_in_progress,
    'parcours_doctoral.change_jury': is_part_of_education_group & is_jury_in_progress,
    # -- Défense
    # -- Soutenance
    # -- Commentaire
    'parcours_doctoral.view_comments': is_part_of_education_group,
    'parcours_doctoral.change_comments': is_part_of_education_group,
}
