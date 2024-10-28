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
from admission.auth.predicates.common import is_part_of_education_group
from admission.auth.predicates.doctorate import (
    is_enrolled,
    is_pre_admission,
)
from osis_role import role
from parcours_doctoral.auth.predicates.parcours_doctoral import submitted_confirmation_paper, \
    complementary_training_enabled, is_jury_in_progress
from parcours_doctoral.auth.roles.cdd_configurator import CddConfigurator
from parcours_doctoral.auth.roles.jury_secretary import JurySecretary

role.role_manager.register(CddConfigurator)
role.role_manager.register(JurySecretary)


def base_program_manager_rules():
    return {
        # Doctorats
        # --- Confirmation
        'admission.view_admission_confirmation': is_part_of_education_group & is_enrolled,
        'admission.change_admission_confirmation': is_part_of_education_group & is_enrolled,
        'admission.change_admission_confirmation_extension': is_part_of_education_group & is_enrolled,
        'admission.make_confirmation_decision': is_part_of_education_group & submitted_confirmation_paper,
        'admission.send_message': is_part_of_education_group & is_enrolled,
        # -- Formation doctorale
        'admission.view_training': is_part_of_education_group & is_enrolled,
        'admission.view_doctoral_training': is_part_of_education_group & is_enrolled & ~is_pre_admission,
        'admission.view_complementary_training': is_part_of_education_group & complementary_training_enabled,
        'admission.view_course_enrollment': is_part_of_education_group & is_enrolled,
        'admission.change_activity': is_part_of_education_group & is_enrolled,
        'admission.delete_activity': is_part_of_education_group & is_enrolled,
        'admission.refuse_activity': is_part_of_education_group & is_enrolled,
        'admission.restore_activity': is_part_of_education_group & is_enrolled,
        # -- Jury
        'admission.view_admission_jury': is_part_of_education_group & is_enrolled & is_jury_in_progress,
        'admission.change_admission_jury': is_part_of_education_group & is_enrolled & is_jury_in_progress,
        # -- Défense
        # -- Soutenance
    }