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
from osis_role.contrib.models import RoleModel
from rules import RuleSet, always_allow

from parcours_doctoral.auth.predicates.parcours_doctoral import (
    complementary_training_enabled,
    confirmation_paper_in_progress,
    is_jury_in_progress,
    is_parcours_doctoral_promoter,
    is_parcours_doctoral_reference_promoter,
)


class Promoter(RoleModel):
    """
    Promoteur

    Le promoteur intervient dans plusieurs processus.
    Un promoteur peut être dit "de référence" pour un doctorat donné, il a alors des actions supplémentaires
    à réaliser (spécifier l'institut de la thèse, donner son accord sur les activités de formation doctorale, etc.).
    """

    class Meta:
        verbose_name = _("Role: Promoter")
        verbose_name_plural = _("Role: Promoters")
        group_name = "promoters"

    @classmethod
    def rule_set(cls):
        rules = {
            'parcours_doctoral.view_supervised_list': always_allow,
            'parcours_doctoral.view_parcours_doctoral': is_parcours_doctoral_promoter,
            'parcours_doctoral.download_pdf_confirmation': is_parcours_doctoral_promoter,
            'parcours_doctoral.approve_confirmation_paper': is_parcours_doctoral_promoter,
            'parcours_doctoral.validate_doctoral_training': is_parcours_doctoral_promoter,
            'parcours_doctoral.fill_thesis': is_parcours_doctoral_promoter,
            'parcours_doctoral.check_publication_authorisation': is_parcours_doctoral_promoter,
            # A promoter can view as long as he is one of the PhD promoters
            'parcours_doctoral.view_project': is_parcours_doctoral_promoter,
            'parcours_doctoral.view_cotutelle': is_parcours_doctoral_promoter,
            'parcours_doctoral.view_funding': is_parcours_doctoral_promoter,
            'parcours_doctoral.view_supervision': is_parcours_doctoral_promoter,
            'parcours_doctoral.view_jury': is_parcours_doctoral_promoter,
            'parcours_doctoral.view_confirmation': is_parcours_doctoral_promoter,
            'parcours_doctoral.upload_pdf_confirmation': is_parcours_doctoral_promoter,
            'parcours_doctoral.change_jury': is_parcours_doctoral_promoter & is_jury_in_progress,
            # PhD training
            'parcours_doctoral.view_complementary_training': is_parcours_doctoral_promoter
            & complementary_training_enabled,
            'parcours_doctoral.view_course_enrollment': is_parcours_doctoral_promoter,
            'parcours_doctoral.view_training': is_parcours_doctoral_promoter,
            'parcours_doctoral.assent_training': is_parcours_doctoral_reference_promoter,
        }
        return RuleSet(rules)
