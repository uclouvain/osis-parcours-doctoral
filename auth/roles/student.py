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
from django.db.models import UniqueConstraint
from django.utils.translation import gettext_lazy as _
from rules import RuleSet, always_allow

from osis_role.contrib.models import RoleModel
from parcours_doctoral.auth.predicates import parcours_doctoral


class Student(RoleModel):
    """
    Étudiant
    """

    class Meta:
        verbose_name = _("Role: Student")
        verbose_name_plural = _("Role: Student")
        group_name = "students"
        constraints = [
            UniqueConstraint(fields=['person'], name='unique_doctorate_student'),
        ]

    @classmethod
    def rule_set(cls):
        rules = {
            'parcours_doctoral.api_view_list': always_allow,
            'parcours_doctoral.api_view_parcours_doctoral': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.api_view_project': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.api_view_funding': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.api_change_funding': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.api_view_cotutelle': parcours_doctoral.is_parcours_doctoral_student
            & parcours_doctoral.is_related_to_an_admission,
            'parcours_doctoral.api_change_cotutelle': parcours_doctoral.is_parcours_doctoral_student
            & parcours_doctoral.is_related_to_an_admission,
            'parcours_doctoral.api_view_supervision': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.api_view_supervision_canvas': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.api_view_confirmation': parcours_doctoral.is_parcours_doctoral_student
            & parcours_doctoral.is_related_to_an_admission,
            # Can edit while the jury is not submitted
            'parcours_doctoral.api_view_jury': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.api_change_jury': parcours_doctoral.is_parcours_doctoral_student
            & parcours_doctoral.is_jury_in_progress,
            'parcours_doctoral.api_change_jury_role': parcours_doctoral.is_parcours_doctoral_student
            & parcours_doctoral.is_jury_in_progress,
            'parcours_doctoral.api_request_signatures': parcours_doctoral.is_parcours_doctoral_student
            & parcours_doctoral.is_jury_in_progress,
            'parcours_doctoral.api_resend_external_invitation': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.api_approve_jury_by_pdf': parcours_doctoral.is_parcours_doctoral_student
            & parcours_doctoral.is_jury_signing_in_progress,
            # Training
            'parcours_doctoral.api_view_complementary_training': parcours_doctoral.is_parcours_doctoral_student
            & parcours_doctoral.complementary_training_enabled,
            'parcours_doctoral.api_view_course_enrollment': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.api_view_doctoral_training': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.api_view_assessment_enrollment': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.api_add_training': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.api_update_training': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.api_submit_training': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.api_view_training': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.api_delete_training': parcours_doctoral.is_parcours_doctoral_student,
            # Once the confirmation paper is in progress, he can
            'parcours_doctoral.api_change_confirmation': parcours_doctoral.is_parcours_doctoral_student
            & parcours_doctoral.confirmation_paper_in_progress
            & parcours_doctoral.is_related_to_an_admission,
            'parcours_doctoral.api_change_confirmation_extension': parcours_doctoral.is_parcours_doctoral_student
            & parcours_doctoral.confirmation_paper_in_progress
            & parcours_doctoral.is_related_to_an_admission,
            # Admissibility
            'parcours_doctoral.api_view_admissibility': parcours_doctoral.is_parcours_doctoral_student
            & parcours_doctoral.defense_method_is_formula_2,
            'parcours_doctoral.api_change_admissibility': parcours_doctoral.is_parcours_doctoral_student
            & parcours_doctoral.defense_method_is_formula_2
            & parcours_doctoral.admissibility_in_progress,
            # Private defense
            'parcours_doctoral.api_retrieve_private_defenses': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.api_view_private_defense': parcours_doctoral.is_parcours_doctoral_student
            & parcours_doctoral.defense_method_is_formula_1,
            'parcours_doctoral.api_change_private_defense': parcours_doctoral.is_parcours_doctoral_student
            & parcours_doctoral.defense_method_is_formula_1
            & parcours_doctoral.private_defense_in_progress,
            # Authorization distribution
            'parcours_doctoral.api_view_authorization_distribution': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.api_change_authorization_distribution': parcours_doctoral.is_parcours_doctoral_student
            & parcours_doctoral.authorization_distribution_can_be_changed_by_student
            & parcours_doctoral.authorization_distribution_is_in_progress,
            # Manuscript validation
            'parcours_doctoral.api_view_manuscript_validation': parcours_doctoral.is_parcours_doctoral_student,
            # Public defense
            'parcours_doctoral.api_view_public_defense': parcours_doctoral.is_parcours_doctoral_student
            & parcours_doctoral.defense_method_is_formula_1,
            'parcours_doctoral.api_change_public_defense': parcours_doctoral.is_parcours_doctoral_student
            & parcours_doctoral.defense_method_is_formula_1
            & parcours_doctoral.public_defense_in_progress,
            # Private and public defenses
            'parcours_doctoral.api_view_private_public_defenses': parcours_doctoral.is_parcours_doctoral_student
            & parcours_doctoral.defense_method_is_formula_2,
            'parcours_doctoral.api_change_private_public_defenses': parcours_doctoral.is_parcours_doctoral_student
            & parcours_doctoral.defense_method_is_formula_2
            & parcours_doctoral.private_public_defenses_are_in_progress_formula_2,
        }
        return RuleSet(rules)
