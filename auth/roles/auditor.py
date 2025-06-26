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
from django.db import models
from django.utils.translation import gettext_lazy as _
from rules import RuleSet

from base.models.entity import Entity
from base.models.enums.organization_type import MAIN
from osis_role.contrib.models import RoleModel


class Auditor(RoleModel):
    """
    Vérificateur.trice

    Valide les jurys de son institut.
    """

    entity = models.OneToOneField(
        Entity,
        on_delete=models.CASCADE,
        related_name='+',
        limit_choices_to={'organization__type': MAIN},
    )

    class Meta:
        verbose_name = _("Role: Auditor")
        group_name = "auditor"

    @classmethod
    def rule_set(cls):
        ruleset = {
            'parcours_doctoral.view_jury': rules.always_allow,
        }
        return RuleSet(ruleset)
