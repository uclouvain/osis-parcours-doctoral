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

from admission.auth.roles.promoter import Promoter as AdmissionPromoter
from parcours_doctoral.auth.predicates.parcours_doctoral import (
    complementary_training_enabled,
    is_jury_in_progress,
    is_jury_signing_in_progress,
    is_parcours_doctoral_promoter,
    is_parcours_doctoral_reference_promoter,
    is_related_to_an_admission,
)


class Promoter(AdmissionPromoter):
    """
    Promoteur

    Le promoteur intervient dans plusieurs processus.
    Un promoteur peut être dit "de référence" pour un doctorat donné, il a alors des actions supplémentaires
    à réaliser (spécifier l'institut de la thèse, donner son accord sur les activités de formation doctorale, etc.).
    """

    class Meta:
        group_name = "promoters"
        proxy = True

    @classmethod
    def rule_set(cls):
        rules = {
            'parcours_doctoral.api_view_supervised_list': always_allow,
            'parcours_doctoral.api_view_parcours_doctoral': is_parcours_doctoral_promoter,
            'parcours_doctoral.api_download_pdf_confirmation': is_parcours_doctoral_promoter
            & is_related_to_an_admission,
            'parcours_doctoral.api_approve_confirmation_paper': is_parcours_doctoral_promoter
            & is_related_to_an_admission,
            'parcours_doctoral.api_validate_doctoral_training': is_parcours_doctoral_promoter,
            'parcours_doctoral.api_fill_thesis': is_parcours_doctoral_promoter,
            # A promoter can view as long as he is one of the PhD promoters
            'parcours_doctoral.api_view_project': is_parcours_doctoral_promoter,
            'parcours_doctoral.api_view_cotutelle': is_parcours_doctoral_promoter & is_related_to_an_admission,
            'parcours_doctoral.api_view_funding': is_parcours_doctoral_promoter,
            'parcours_doctoral.api_view_supervision': is_parcours_doctoral_promoter,
            'parcours_doctoral.api_view_supervision_canvas': is_parcours_doctoral_reference_promoter,
            'parcours_doctoral.api_view_jury': is_parcours_doctoral_promoter,
            'parcours_doctoral.api_view_confirmation': is_parcours_doctoral_promoter & is_related_to_an_admission,
            'parcours_doctoral.api_upload_pdf_confirmation': is_parcours_doctoral_promoter & is_related_to_an_admission,
            'parcours_doctoral.api_change_jury': is_parcours_doctoral_reference_promoter & is_jury_in_progress,
            'parcours_doctoral.api_change_jury_role': is_parcours_doctoral_reference_promoter
            & is_jury_signing_in_progress,
            'parcours_doctoral.api_approve_jury': is_jury_signing_in_progress,
            # PhD training
            'parcours_doctoral.api_view_complementary_training': is_parcours_doctoral_promoter
            & complementary_training_enabled,
            'parcours_doctoral.api_view_course_enrollment': is_parcours_doctoral_promoter,
            'parcours_doctoral.api_view_training': is_parcours_doctoral_promoter,
            'parcours_doctoral.api_assent_training': is_parcours_doctoral_reference_promoter,
            # Private defense
            'parcours_doctoral.api_view_private_defense': is_parcours_doctoral_promoter,
            'parcours_doctoral.api_view_private_defense_minutes': is_parcours_doctoral_promoter,
        }
        return RuleSet(rules)
