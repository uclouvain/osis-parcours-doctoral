# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
from typing import List

from django.utils.translation import gettext_lazy as _

from parcours_doctoral.ddd.formation.domain.model.enums import (
    CategorieActivite,
    ChoixTypeEpreuve,
    StatutActivite,
)
from parcours_doctoral.models import Activity


def training_categories_activities(activities: List[Activity]):
    categories = {
        _("Participations"): [],
        _("Scientific communications"): [],
        _("Publications"): [],
        _("Followed courses"): [],
        _("Services"): [],
        _("VAE"): [],
        _("Scientific residencies"): [],
        _("Confirmation exam"): [],
        _("Thesis defense"): [],
        _("Total"): [],
    }
    for activity in activities:
        if activity.status not in [StatutActivite.SOUMISE.name, StatutActivite.ACCEPTEE.name]:
            continue

        if (
            activity.category == CategorieActivite.CONFERENCE.name
            or activity.category == CategorieActivite.SEMINAR.name
        ):
            categories[_("Participations")].append(activity)
        elif activity.category == CategorieActivite.COMMUNICATION.name and (
            activity.parent_id is None or activity.parent.category == CategorieActivite.CONFERENCE.name
        ):
            categories[_("Scientific communications")].append(activity)
        elif activity.category == CategorieActivite.PUBLICATION.name and (
            activity.parent_id is None or activity.parent.category == CategorieActivite.CONFERENCE.name
        ):
            categories[_("Publications")].append(activity)
        elif activity.category == CategorieActivite.SERVICE.name:
            categories[_("Services")].append(activity)
        elif (
            activity.category == CategorieActivite.RESIDENCY.name
            or activity.parent_id
            and activity.parent.category == CategorieActivite.RESIDENCY.name
        ):
            categories[_("Scientific residencies")].append(activity)
        elif activity.category == CategorieActivite.VAE.name:
            categories[_("VAE")].append(activity)
        elif activity.category in [CategorieActivite.COURSE.name, CategorieActivite.UCL_COURSE.name]:
            categories[_("Followed courses")].append(activity)
        elif (
            activity.category == CategorieActivite.PAPER.name
            and activity.type == ChoixTypeEpreuve.CONFIRMATION_PAPER.name
        ):
            categories[_("Confirmation exam")].append(activity)
        elif activity.category == CategorieActivite.PAPER.name:
            categories[_("Thesis defense")].append(activity)
    return categories


def training_categories_stats(activities: List[Activity]):
    submitted, validated = 0, 0
    categories = training_categories_activities(activities)

    for category, category_activities in categories.items():
        category_submitted = sum(
            activity.ects for activity in category_activities if activity.status != StatutActivite.ACCEPTEE.name
        )
        category_validated = sum(
            activity.ects for activity in category_activities if activity.status == StatutActivite.ACCEPTEE.name
        )
        categories[category] = [category_submitted, category_validated]
        submitted += category_submitted
        validated += category_validated
    categories[_("Total")] = [submitted, validated]

    return submitted + validated, validated, categories
