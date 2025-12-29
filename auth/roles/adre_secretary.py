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
    authorization_distribution_can_be_changed_by_adre,
    authorization_distribution_is_in_progress,
    defense_method_is_formula_1_or_unknown,
    defense_method_is_formula_2,
    has_valid_enrollment,
    is_related_to_an_admission,
)


class AdreSecretary(RoleModel):
    """
    Secrétaire ADRE

    Intervient pour télécharger/-verser des documents (ex : demande de renouvellement de bourse lors de la confirmation)
    et pour vérifier la pertinence de la publication de la thèse.
    """

    class Meta:
        verbose_name = _("Role: ADRE secretary")
        verbose_name_plural = _("Role: ADRE Secretaries")
        group_name = "adre_secretary"

    @classmethod
    def rule_set(cls):
        ruleset = {
            'base.can_access_student_path': rules.always_allow,
            # Doctorate
            'parcours_doctoral.view_parcours_doctoral': rules.always_allow,
            'parcours_doctoral.view_parcours_doctoral_home': rules.always_allow,
            'parcours_doctoral.view_project': rules.always_allow,
            'parcours_doctoral.view_funding': rules.always_allow,
            'parcours_doctoral.view_cotutelle': is_related_to_an_admission,
            'parcours_doctoral.view_jury': rules.always_allow,
            'parcours_doctoral.view_confirmation': rules.always_allow,
            'parcours_doctoral.upload_pdf_confirmation': is_related_to_an_admission & has_valid_enrollment,
            'parcours_doctoral.view_supervision': rules.always_allow,
            'parcours_doctoral.view_documents': rules.always_allow,
            'parcours_doctoral.view_historyentry': rules.always_allow,
            'parcours_doctoral.send_message': rules.always_allow,
            'parcours_doctoral.view_comments': rules.always_allow,
            'parcours_doctoral.view_training': rules.always_allow,
            'parcours_doctoral.view_doctoral_training': rules.always_allow,
            'parcours_doctoral.view_complementary_training': rules.always_allow,
            'parcours_doctoral.view_course_enrollment': rules.always_allow,
            'parcours_doctoral.view_assessment_enrollment': rules.always_allow,
            'parcours_doctoral.view_private_defense': defense_method_is_formula_1_or_unknown,
            'parcours_doctoral.view_public_defense': defense_method_is_formula_1_or_unknown,
            'parcours_doctoral.view_admissibility': defense_method_is_formula_2,
            'parcours_doctoral.view_private_public_defenses': defense_method_is_formula_2,
            'parcours_doctoral.view_authorization_distribution': rules.always_allow,
            'parcours_doctoral.view_manuscript_validation': rules.always_allow,
            'parcours_doctoral.validate_manuscript': has_valid_enrollment
            & authorization_distribution_can_be_changed_by_adre
            & authorization_distribution_is_in_progress,
        }
        return RuleSet(ruleset)
