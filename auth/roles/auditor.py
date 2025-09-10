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

from osis_role.contrib.models import EntityRoleModel
from parcours_doctoral.auth.predicates.parcours_doctoral import (
    is_jury_signing_in_progress,
    is_part_of_jury,
)


class Auditor(EntityRoleModel):
    """
    Vérificateur.trice

    Valide les jurys de son institut.
    """

    class Meta:
        verbose_name = _("Role: Auditor")
        group_name = "auditor"

    @classmethod
    def rule_set(cls):
        ruleset = {
            'parcours_doctoral.api_view_parcours_doctoral': is_part_of_jury,
            'parcours_doctoral.api_view_jury': is_part_of_jury,
            'parcours_doctoral.api_approve_jury': is_part_of_jury & is_jury_signing_in_progress,
            'parcours_doctoral.api_change_jury_role': is_part_of_jury & is_jury_signing_in_progress,
        }
        return RuleSet(ruleset)
