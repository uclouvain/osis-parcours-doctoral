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
    is_related_to_an_admission,
)


class JurySecretary(RoleModel):
    """
    Secrétaire de Jury

    Le secrétaire/président du jury intervient pour acter les décisions du jury lors de la défense privée
    et la soutenance.
    """

    class Meta:
        verbose_name = _("Role: Jury secretary")
        verbose_name_plural = _("Role: Jury secretaries")
        group_name = "jury_secretary"

    @classmethod
    def rule_set(cls):
        ruleset = {
            'parcours_doctoral.upload_defense_report': has_valid_enrollment,
            'parcours_doctoral.view_doctorateadmission': rules.always_allow,
            'parcours_doctoral.view_person': rules.always_allow,
            'parcours_doctoral.view_coordinates': rules.always_allow,
            'parcours_doctoral.view_secondary_studies': rules.always_allow,
            'parcours_doctoral.view_curriculum': rules.always_allow,
            'parcours_doctoral.view_project': rules.always_allow,
            'parcours_doctoral.view_cotutelle': is_related_to_an_admission,
            'parcours_doctoral.view_supervision': rules.always_allow,
            'parcours_doctoral.view_jury': rules.always_allow,
        }
        return RuleSet(ruleset)
