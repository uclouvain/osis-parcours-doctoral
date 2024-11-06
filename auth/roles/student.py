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
from rules import RuleSet, always_allow

from osis_role.contrib.models import RoleModel
from parcours_doctoral.auth.predicates import parcours_doctoral


class Student(RoleModel):
    """
    Étudiant
    """

    class Meta:
        verbose_name = _("Role: Student")
        verbose_name_plural = _("Role: Student")
        group_name = "students"

    @classmethod
    def rule_set(cls):
        rules = {
            'parcours_doctoral.view_list': always_allow,
            'parcours_doctoral.view_parcours_doctoral': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.view_project': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.view_funding': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.change_funding': parcours_doctoral.is_parcours_doctoral_student,
            # Can edit while the jury is not submitted
            'parcours_doctoral.view_admission_jury': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.change_admission_jury': parcours_doctoral.is_parcours_doctoral_student
            & parcours_doctoral.is_jury_in_progress,
            'parcours_doctoral.view_complementary_training': parcours_doctoral.is_parcours_doctoral_student
            & parcours_doctoral.complementary_training_enabled,
            'parcours_doctoral.view_course_enrollment': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.add_training': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.update_training': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.submit_training': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.view_training': parcours_doctoral.is_parcours_doctoral_student,
            'parcours_doctoral.delete_training': parcours_doctoral.is_parcours_doctoral_student,
            # Once the confirmation paper is in progress, he can
            'parcours_doctoral.change_admission_confirmation': parcours_doctoral.is_parcours_doctoral_student
            & parcours_doctoral.confirmation_paper_in_progress,
            'parcours_doctoral.change_admission_confirmation_extension': parcours_doctoral.is_parcours_doctoral_student
            & parcours_doctoral.confirmation_paper_in_progress,
        }
        return RuleSet(rules)
