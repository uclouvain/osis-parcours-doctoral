# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from django import template
from django.utils.translation import gettext_lazy as _

from parcours_doctoral.ddd.formation.domain.model.enums import (
    CategorieActivite,
    ChoixTypeEpreuve,
    StatutActivite,
)

register = template.Library()


@register.filter
def status_list(admission):
    statuses = {str(admission.status)}
    for child in admission.children.all():
        statuses.add(str(child.status))
    return ','.join(statuses)


@register.filter
def status_as_class(activity):
    return {
        StatutActivite.SOUMISE.name: "warning",
        StatutActivite.ACCEPTEE.name: "success",
        StatutActivite.REFUSEE.name: "danger",
    }.get(getattr(activity, 'status', activity), 'info')


@register.inclusion_tag('admission/doctorate/includes/training_categories.html')
def training_categories(activities):
    added, validated = 0, 0

    categories = {
        _("Participation to symposium/conference"): [0, 0],
        _("Oral communication"): [0, 0],
        _("Seminar taken"): [0, 0],
        _("Publications"): [0, 0],
        _("Courses taken"): [0, 0],
        _("Services"): [0, 0],
        _("VAE"): [0, 0],
        _("Scientific residencies"): [0, 0],
        _("Confirmation exam"): [0, 0],
        _("Thesis defense"): [0, 0],
    }
    for activity in activities:
        # Increment global counts
        if activity.status != StatutActivite.REFUSEE.name:
            added += activity.ects
        if activity.status == StatutActivite.ACCEPTEE.name:
            validated += activity.ects
        if activity.status not in [StatutActivite.SOUMISE.name, StatutActivite.ACCEPTEE.name]:
            continue

        # Increment category counts
        index = int(activity.status == StatutActivite.ACCEPTEE.name)
        if activity.category == CategorieActivite.CONFERENCE.name:
            categories[_("Participation to symposium/conference")][index] += activity.ects
        elif activity.category == CategorieActivite.SEMINAR.name:
            categories[_("Seminar taken")][index] += activity.ects
        elif activity.category == CategorieActivite.COMMUNICATION.name and (
            activity.parent_id is None or activity.parent.category == CategorieActivite.CONFERENCE.name
        ):
            categories[_("Oral communication")][index] += activity.ects
        elif activity.category == CategorieActivite.PUBLICATION.name and (
            activity.parent_id is None or activity.parent.category == CategorieActivite.CONFERENCE.name
        ):
            categories[_("Publications")][index] += activity.ects
        elif activity.category == CategorieActivite.SERVICE.name:
            categories[_("Services")][index] += activity.ects
        elif (
            activity.category == CategorieActivite.RESIDENCY.name
            or activity.parent_id
            and activity.parent.category == CategorieActivite.RESIDENCY.name
        ):
            categories[_("Scientific residencies")][index] += activity.ects
        elif activity.category == CategorieActivite.VAE.name:
            categories[_("VAE")][index] += activity.ects
        elif activity.category in [CategorieActivite.COURSE.name, CategorieActivite.UCL_COURSE.name]:
            categories[_("Courses taken")][index] += activity.ects
        elif (
            activity.category == CategorieActivite.PAPER.name
            and activity.type == ChoixTypeEpreuve.CONFIRMATION_PAPER.name
        ):
            categories[_("Confirmation exam")][index] += activity.ects
        elif activity.category == CategorieActivite.PAPER.name:
            categories[_("Thesis defense")][index] += activity.ects
    if not added:
        return {}
    return {
        'display_table': any(cat_added + cat_validated for cat_added, cat_validated in categories.values()),
        'categories': categories,
        'added': added,
        'validated': validated,
    }
