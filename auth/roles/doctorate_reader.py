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

from django.utils.translation import gettext_lazy as _
from rules import RuleSet, always_allow

from osis_role.contrib.models import RoleModel
from parcours_doctoral.auth.predicates.parcours_doctoral import (
    defense_method_is_formula_1,
    defense_method_is_formula_2,
    is_related_to_an_admission,
)


class DoctorateReader(RoleModel):
    class Meta:
        verbose_name = _("Role: Doctorate reader")
        verbose_name_plural = _("Role: Doctorate readers")
        group_name = "doctorate_reader"

    @classmethod
    def rule_set(cls):
        ruleset = {
            'base.can_access_student_path': always_allow,
            'parcours_doctoral.view_parcours_doctoral_home': always_allow,
            'parcours_doctoral.view_parcours_doctoral': always_allow,
            'parcours_doctoral.view_project': always_allow,
            'parcours_doctoral.view_funding': always_allow,
            'parcours_doctoral.view_cotutelle': is_related_to_an_admission,
            'parcours_doctoral.view_supervision': always_allow,
            'parcours_doctoral.view_historyentry': always_allow,
            'parcours_doctoral.view_comments': always_allow,
            'parcours_doctoral.view_documents': always_allow,
            'parcours_doctoral.view_training': always_allow,
            'parcours_doctoral.view_doctoral_training': always_allow,
            'parcours_doctoral.view_complementary_training': always_allow,
            'parcours_doctoral.view_course_enrollment': always_allow,
            'parcours_doctoral.view_assessment_enrollment': always_allow,
            'parcours_doctoral.view_confirmation': is_related_to_an_admission,
            'parcours_doctoral.view_jury': always_allow,
            'parcours_doctoral.view_private_defense': defense_method_is_formula_1,
            'parcours_doctoral.view_public_defense': defense_method_is_formula_1,
            'parcours_doctoral.view_admissibility': defense_method_is_formula_2,
            'parcours_doctoral.view_private_public_defenses': defense_method_is_formula_2,
            'parcours_doctoral.view_authorization_distribution': always_allow,
            'parcours_doctoral.view_manuscript_validation': always_allow,
        }
        return RuleSet(ruleset)
