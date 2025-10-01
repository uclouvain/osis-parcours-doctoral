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

import rules
from django.utils.translation import gettext_lazy as _
from rules import RuleSet

from osis_role.contrib.models import RoleModel
from parcours_doctoral.auth.predicates.parcours_doctoral import (
    has_valid_enrollment,
    is_jury_approuve_cdd,
    is_related_to_an_admission,
)


class AdreManager(RoleModel):
    """
    Getionnaire ADRE
    """

    class Meta:
        verbose_name = _("Role: ADRE manager")
        verbose_name_plural = _("Role: ADRE managers")
        group_name = "adre_manager"

    @classmethod
    def rule_set(cls):
        ruleset = {
            # Doctorate
            'parcours_doctoral.view_parcours_doctoral': rules.always_allow,
            'parcours_doctoral.view_person': rules.always_allow,
            'parcours_doctoral.view_coordinates': rules.always_allow,
            'parcours_doctoral.view_secondary_studies': rules.always_allow,
            'parcours_doctoral.view_curriculum': rules.always_allow,
            'parcours_doctoral.view_project': rules.always_allow,
            'parcours_doctoral.view_cotutelle': is_related_to_an_admission,
            'parcours_doctoral.view_jury': rules.always_allow,
            'parcours_doctoral.view_languages': rules.always_allow,
            'parcours_doctoral.view_confirmation': is_related_to_an_admission,
            'parcours_doctoral.view_supervision': rules.always_allow,
            'parcours_doctoral.view_historyentry': rules.always_allow,
            'parcours_doctoral.view_internalnote': rules.always_allow,
            'parcours_doctoral.view_training': rules.always_allow,
            'parcours_doctoral.view_doctoral_training': rules.always_allow,
            'parcours_doctoral.view_complementary_training': rules.always_allow,
            'parcours_doctoral.view_course_enrollment': rules.always_allow,
            'parcours_doctoral.approve_jury': is_jury_approuve_cdd,
        }
        return RuleSet(ruleset)
