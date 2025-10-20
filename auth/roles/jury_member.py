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
from parcours_doctoral.auth.predicates.parcours_doctoral import (
    is_jury_signing_in_progress,
    is_part_of_jury,
    is_related_to_an_admission,
)


class JuryMember(RoleModel):
    """
    Membre du jury du doctorand.
    """

    class Meta:
        verbose_name = _("Role: Jury member")
        verbose_name_plural = _("Role: Jury members")
        group_name = "jury_members"
        constraints = [UniqueConstraint(fields=['person'], name='parcours_doctoral_unique_jury_member_by_person')]

    @classmethod
    def rule_set(cls):
        ruleset = {
            # A jury member can view as long as he belongs to the jury
            'parcours_doctoral.api_view_parcours_doctoral': is_part_of_jury,
            'parcours_doctoral.api_view_project': is_part_of_jury,
            'parcours_doctoral.api_view_cotutelle': is_part_of_jury & is_related_to_an_admission,
            'parcours_doctoral.api_view_funding': is_part_of_jury,
            'parcours_doctoral.api_view_supervision': is_part_of_jury,
            'parcours_doctoral.api_view_confirmation': is_part_of_jury & is_related_to_an_admission,
            'parcours_doctoral.api_view_jury': is_part_of_jury,
            'parcours_doctoral.api_approve_jury': is_part_of_jury & is_jury_signing_in_progress,
        }
        return RuleSet(ruleset)
