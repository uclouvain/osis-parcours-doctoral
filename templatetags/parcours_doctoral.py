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
from dataclasses import dataclass

from django import template
from django.utils.translation import gettext_lazy as _, pgettext
import re

from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from parcours_doctoral.constants import CAMPUSES_UUIDS
from parcours_doctoral.ddd.dtos import CampusDTO
from parcours_doctoral.ddd.formation.domain.model.enums import (
    CategorieActivite,
    ChoixTypeEpreuve,
    StatutActivite,
)

register = template.Library()


@dataclass
class Tab:
    name: str
    label: str = ''
    icon: str = ''
    badge: str = ''

    def __hash__(self):
        # Only hash the name, as lazy strings have different memory addresses
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name


TAB_TREE = {
    # Tab('documents', _('Documents'), 'folder-open'): [
    #     Tab('documents', _('Documents'), 'folder-open'),
    # ],
    # Tab('comments', pgettext('tab', 'Comments'), 'comments'): [
    #     Tab('comments', pgettext('tab', 'Comments'), 'comments')
    # ],
    # Tab('history', pgettext('tab', 'History'), 'history'): [
    #     Tab('history-all', _('All history')),
    #     Tab('history', _('Status changes')),
    # ],
    # Tab('person', _('Personal data'), 'user'): [
    #     Tab('person', _('Identification'), 'user'),
    #     Tab('coordonnees', _('Contact details'), 'user'),
    # ],
    # Tab('experience', _('Previous experience'), 'list-alt'): [
    #     Tab('curriculum', _('Curriculum')),
    #     Tab('languages', _('Knowledge of languages')),
    # ],
    # Tab('doctorate', pgettext('tab', 'PhD project'), 'graduation-cap'): [
    #     Tab('project', pgettext('tab', 'Research project')),
    #     Tab('cotutelle', _('Cotutelle')),
    #     Tab('supervision', _('Supervision')),
    # ],
    # Tab('additional-information', _('Additional information'), 'puzzle-piece'): [
    #     Tab('accounting', _('Accounting')),
    # ],
    Tab('confirmation', pgettext('tab', 'Confirmation'), 'award'): [
        Tab('confirmation', _('Confirmation exam')),
        Tab('extension-request', _('New deadline')),
    ],
    # Tab('training', pgettext('admission', 'Course'), 'book-open-reader'): [
    #     Tab('doctoral-training', _('PhD training')),
    #     Tab('complementary-training', _('Complementary training')),
    #     Tab('course-enrollment', _('Course unit enrolment')),
    # ],
    Tab('defense', pgettext('doctorate tab', 'Defense'), 'person-chalkboard'): [
        Tab('jury-preparation', pgettext('admission tab', 'Defense method')),
        Tab('jury', _('Jury composition')),
    ],
    # Tab('management', pgettext('tab', 'Management'), 'gear'): [
    #     Tab('send-mail', _('Send a mail')),
    #     Tab('debug', _('Debug'), 'bug'),
    # ],
}


def get_active_parent(tab_tree, tab_name):
    return next(
        (parent for parent, children in tab_tree.items() if any(child.name == tab_name for child in children)),
        None,
    )

@register.simple_tag(takes_context=True)
def default_tab_context(context):
    match = context['request'].resolver_match
    active_tab = match.url_name
    active_parent = get_active_parent(TAB_TREE, active_tab)

    return {
        'active_parent': active_parent,
        'active_tab': active_tab,
        'parcours_doctoral_uuid': context['view'].kwargs.get('uuid', ''),
        'namespace': ':'.join(match.namespaces[:2]),
        'request': context['request'],
        'view': context['view'],
    }









@register.inclusion_tag('admission/includes/admission_tabs_bar.html', takes_context=True)
def admission_tabs(context):
    tab_context = default_tab_context(context)
    admission = context['view'].get_permission_object()
    current_tab_tree = get_valid_tab_tree(context, admission, TAB_TREES[get_current_context(admission)]).copy()
    tab_context['tab_tree'] = current_tab_tree
    return tab_context


@register.inclusion_tag('admission/includes/subtabs_bar.html', takes_context=True)
def subtabs_bar(context):
    return current_subtabs(context)


@register.simple_tag(takes_context=True)
def current_subtabs(context):
    tab_context = default_tab_context(context)
    permission_obj = context['view'].get_permission_object()
    tab_tree = TAB_TREES[get_current_context(admission=permission_obj)]
    tab_context['subtabs'] = (
        [tab for tab in tab_tree[tab_context['active_parent']] if can_read_tab(context, tab.name, permission_obj)]
        if tab_context['active_parent']
        else []
    )
    return tab_context


@register.simple_tag(takes_context=True)
def has_perm(context, perm, obj=None):
    if not obj:
        obj = context['view'].get_permission_object()
    perm = perm % {'[context]': PERMISSION_BY_ADMISSION_CLASS[type(obj)]}
    return rules.has_perm(perm, context['request'].user, obj)



@register.simple_tag(takes_context=True)
def can_read_tab(context, tab_name, obj=None):
    """Return true if the specified tab can be opened in reading mode for this admission, otherwise return False"""
    return has_perm(context, READ_ACTIONS_BY_TAB[tab_name], obj)


@register.simple_tag(takes_context=True)
def can_update_tab(context, tab_name, obj=None):
    """Return true if the specified tab can be opened in update mode for this admission, otherwise return False"""
    return has_perm(context, UPDATE_ACTIONS_BY_TAB[tab_name], obj)


@register.simple_tag(takes_context=True)
def detail_tab_path_from_update(context, admission_uuid):
    """From an update page, get the path of the detail page."""
    match = context['request'].resolver_match
    current_tab_name = match.url_name
    if len(match.namespaces) > 2 and match.namespaces[2] != 'update':
        current_tab_name = match.namespaces[2]
    return reverse(
        '{}:{}'.format(':'.join(match.namespaces[:-1]), current_tab_name),
        args=[admission_uuid],
    )










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


@register.filter
def phone_spaced(phone, with_optional_zero=False):
    if not phone:
        return ""
    # Taken from https://github.com/daviddrysdale/python-phonenumbers/blob/dev/python/phonenumbers/data/region_BE.py#L14
    if with_optional_zero and phone[0] == "0":
        return "(0)" + re.sub('(\\d{2})(\\d{2})(\\d{2})(\\d{2})', '\\1 \\2 \\3 \\4', phone[1:])
    return re.sub('(\\d{3})(\\d{2})(\\d{2})(\\d{2})', '\\1 \\2 \\3 \\4', phone)


@register.simple_tag
def footer_campus(campus: CampusDTO):
    campuses = {
        'LOUVAIN-LA-NEUVE': {
            CAMPUSES_UUIDS['AUTRE_SITE_UUID'],
            CAMPUSES_UUIDS['LOUVAIN_LA_NEUVE_UUID'],
        },
        'BRUXELLES': {
            CAMPUSES_UUIDS['BRUXELLES_WOLUWE_UUID'],
            CAMPUSES_UUIDS['BRUXELLES_SAINT_LOUIS_UUID'],
            CAMPUSES_UUIDS['BRUXELLES_SAINT_GILLES_UUID'],
        },
        'MONS': {
            CAMPUSES_UUIDS['MONS_UUID'],
        },
        'TOURNAI': {
            CAMPUSES_UUIDS['TOURNAI_UUID'],
        },
        'CHARLEROI': {
            CAMPUSES_UUIDS['CHARLEROI_UUID'],
        },
        'NAMUR': {
            CAMPUSES_UUIDS['NAMUR_UUID'],
        },
    }

    return mark_safe(' | '.join(
        f'<strong>{campus_name}</strong>' if campus.uuid in campuses[campus_name] else campus_name
        for campus_name in campuses
    ))


@register.inclusion_tag('parcours_doctoral/includes/field_data.html', takes_context=True)
def field_data(
    context,
    name,
    data=None,
    css_class=None,
    hide_empty=False,
    translate_data=False,
    inline=False,
    html_tag='',
    tooltip=None,
):
    if context.get('all_inline') is True:
        inline = True

    if isinstance(data, list):
        if context.get('hide_files') is True:
            data = None
            hide_empty = True
        elif context.get('load_files') is False:
            data = _('Specified') if data else _('Incomplete field')
        elif data:
            template_string = "{% load osis_document %}{% document_visualizer files for_modified_upload=True %}"
            template_context = {'files': data}
            data = template.Template(template_string).render(template.Context(template_context))
        else:
            data = ''
    elif type(data) == bool:
        data = _('Yes') if data else _('No')
    elif translate_data is True:
        data = _(data)

    if inline is True:
        if name and name[-1] not in ':?!.':
            name = _("%(label)s:") % {'label': name}
        css_class = (css_class + ' inline-field-data') if css_class else 'inline-field-data'

    return {
        'name': name,
        'data': data,
        'css_class': css_class,
        'hide_empty': hide_empty,
        'html_tag': html_tag,
        'inline': inline,
        'tooltip': tooltip,
    }
