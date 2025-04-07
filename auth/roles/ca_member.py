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
from rules import RuleSet, always_allow

from admission.auth.roles.ca_member import CommitteeMember as AdmissionCommitteeMember
from parcours_doctoral.auth.predicates.parcours_doctoral import (
    is_part_of_committee,
    is_related_to_an_admission,
)


class CommitteeMember(AdmissionCommitteeMember):
    """
    Membre du comité

    Membre du comité d'accompagnement du doctorand, il approuve l'admission et le Jury. Dans d'autres processus
    c'est la CDD ou le promoteur qui acte la décision collégiale du comité d'accompagnement dans le système.
    """

    class Meta:
        group_name = "committee_members"
        proxy = True

    @classmethod
    def rule_set(cls):
        ruleset = {
            'parcours_doctoral.view_supervised_list': always_allow,
            # A ca member can view as long as he belongs to the committee
            'parcours_doctoral.view_parcours_doctoral': is_part_of_committee,
            'parcours_doctoral.view_project': is_part_of_committee,
            'parcours_doctoral.view_cotutelle': is_part_of_committee & is_related_to_an_admission,
            'parcours_doctoral.view_funding': is_part_of_committee,
            'parcours_doctoral.view_supervision': is_part_of_committee,
            'parcours_doctoral.view_confirmation': is_part_of_committee & is_related_to_an_admission,
            'parcours_doctoral.view_jury': is_part_of_committee,
            'parcours_doctoral.approve_jury': is_part_of_committee,
        }
        return RuleSet(ruleset)
