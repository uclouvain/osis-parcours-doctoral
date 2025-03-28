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

import rules
from base.models.entity import Entity
from base.models.enums.organization_type import MAIN
from django.db import models
from django.utils.translation import gettext_lazy as _
from osis_role.contrib.models import EntityRoleModel
from rules import RuleSet


class CddConfigurator(EntityRoleModel):
    """
    Configurateur CDD

    Le configurateur CDD met à jour les tables de configuration pour sa CDD
    (menus "Configuration de la CDD" et "Templates d'email de CDD").
    """

    entity = models.ForeignKey(
        Entity,
        on_delete=models.CASCADE,
        related_name='+',
        limit_choices_to={'organization__type': MAIN},
    )

    class Meta:
        verbose_name = _("Role: CDD configurator")
        verbose_name_plural = _("Role: CDD configurators")
        group_name = "cdd_configurators"

    @classmethod
    def rule_set(cls):
        ruleset = {
            'base.can_access_student_path': rules.always_allow,
            'parcours_doctoral.view_cdd_config_home': rules.always_allow,
            'parcours_doctoral.change_cddconfiguration': rules.always_allow,
            'parcours_doctoral.change_cddmailtemplate': rules.always_allow,
        }
        return RuleSet(ruleset)
