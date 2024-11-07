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
from django.utils.translation import gettext_lazy as _
from rules import RuleSet

from osis_role.contrib.models import RoleModel
from parcours_doctoral.auth.predicates.parcours_doctoral import is_part_of_committee


class CommitteeMember(RoleModel):
    """
    Membre du comité

    Membre du comité d'accompagnement du doctorand, il approuve l'admission et le Jury. Dans d'autres processus
    c'est la CDD ou le promoteur qui acte la décision collégiale du comité d'accompagnement dans le système.
    """

    class Meta:
        verbose_name = _("Role: Committee member")
        verbose_name_plural = _("Role: Committee members")
        group_name = "committee_members"

    @classmethod
    def rule_set(cls):
        ruleset = {
            # A ca member can view as long as he belongs to the committee
            'parcours_doctoral.view_parcours_doctoral': is_part_of_committee,
            'parcours_doctoral.view_parcours_doctoral_project': is_part_of_committee,
            'parcours_doctoral.view_parcours_doctoral_cotutelle': is_part_of_committee,
            'parcours_doctoral.view_parcours_doctoral_jury': is_part_of_committee,
            'parcours_doctoral.approve_jury': is_part_of_committee,
            'parcours_doctoral.view_parcours_doctoral_supervision': is_part_of_committee,
            # Once the candidate is enrolling, a ca member can
            'parcours_doctoral.view_parcours_doctoral_confirmation': is_part_of_committee,
        }
        return RuleSet(ruleset)