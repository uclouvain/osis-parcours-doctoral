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
from rules import RuleSet

from osis_role.contrib.models import RoleModel
from parcours_doctoral.auth.predicates.parcours_doctoral import (
    admissibility_is_submitted,
    defense_method_is_formula_1,
    defense_method_is_formula_1_or_unknown,
    defense_method_is_formula_2,
    is_jury_signing_in_progress,
    is_part_of_jury,
    is_president_or_secretary_of_jury,
    is_related_to_an_admission,
    private_defense_is_authorised,
    public_defense_is_authorised,
)


class JuryMember(RoleModel):
    """
    Membre du jury du doctorand.
    """

    class Meta:
        verbose_name = _("Role: Jury member")
        verbose_name_plural = _("Role: Jury members")
        group_name = "doctoral_program_jury_members"
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
            'parcours_doctoral.api_view_confirmation': is_part_of_jury,
            'parcours_doctoral.api_view_complementary_training': is_part_of_jury,
            'parcours_doctoral.api_view_course_enrollment': is_part_of_jury,
            'parcours_doctoral.api_view_training': is_part_of_jury,
            'parcours_doctoral.api_view_doctoral_training': is_part_of_jury,
            'parcours_doctoral.api_view_assessment_enrollment': is_part_of_jury,
            'parcours_doctoral.api_view_jury': is_part_of_jury,
            'parcours_doctoral.api_approve_jury': is_part_of_jury & is_jury_signing_in_progress,
            # Admissibility
            'parcours_doctoral.api_view_admissibility': is_part_of_jury & defense_method_is_formula_2,
            'parcours_doctoral.api_view_admissibility_minutes': is_president_or_secretary_of_jury
            & defense_method_is_formula_2,
            'parcours_doctoral.api_upload_admissibility_minutes_and_opinions': is_president_or_secretary_of_jury
            & defense_method_is_formula_2
            & admissibility_is_submitted,
            # Private defense
            'parcours_doctoral.api_retrieve_private_defenses': is_part_of_jury,
            'parcours_doctoral.api_view_private_defense': is_part_of_jury & defense_method_is_formula_1_or_unknown,
            'parcours_doctoral.api_view_private_defense_minutes': is_president_or_secretary_of_jury,
            'parcours_doctoral.api_upload_private_defense_minutes': is_president_or_secretary_of_jury
            & defense_method_is_formula_1
            & private_defense_is_authorised,
            # Public defense
            'parcours_doctoral.api_view_public_defense': is_part_of_jury & defense_method_is_formula_1_or_unknown,
            'parcours_doctoral.api_view_public_defense_minutes': is_president_or_secretary_of_jury,
            'parcours_doctoral.api_upload_public_defense_minutes': is_president_or_secretary_of_jury
            & defense_method_is_formula_1
            & public_defense_is_authorised,
            # Private & public defenses
            'parcours_doctoral.api_view_private_public_defenses': is_part_of_jury & defense_method_is_formula_2,
            'parcours_doctoral.api_upload_private_public_defense_minutes': is_president_or_secretary_of_jury
            & defense_method_is_formula_2
            & public_defense_is_authorised,
        }
        return RuleSet(ruleset)
