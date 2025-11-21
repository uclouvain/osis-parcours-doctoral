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
import re
from dataclasses import dataclass

import attr
from django import template
from django.conf import settings
from django.core.validators import EMPTY_VALUES
from django.db.models import QuerySet
from django.urls import NoReverseMatch, reverse
from django.utils.safestring import mark_safe
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from django_bootstrap5.renderers import FieldRenderer
from osis_document_components.enums import PostProcessingWanted
from osis_document_components.services import get_remote_metadata, get_remote_token

from base.forms.utils.file_field import PDF_MIME_TYPE
from base.models.entity_version import EntityVersion
from base.models.organization import Organization
from osis_profile.constants import IMAGE_MIME_TYPES
from osis_profile.utils.utils import (
    format_school_title,
    get_superior_institute_queryset,
)
from parcours_doctoral.auth.constants import READ_ACTIONS_BY_TAB, UPDATE_ACTIONS_BY_TAB
from parcours_doctoral.constants import CAMPUSES_UUIDS
from parcours_doctoral.ddd.domain.model.enums import (
    STATUTS_PAR_ETAPE_PARCOURS_DOCTORAL,
    ChoixEtapeParcoursDoctoral,
    ChoixStatutParcoursDoctoral,
)
from parcours_doctoral.ddd.dtos import CampusDTO, ParcoursDoctoralDTO
from parcours_doctoral.ddd.formation.domain.model.enums import StatutActivite
from parcours_doctoral.ddd.jury.dtos.jury import MembreJuryDTO
from parcours_doctoral.ddd.repository.i_parcours_doctoral import formater_reference
from parcours_doctoral.forms.supervision import MemberSupervisionForm
from parcours_doctoral.models import Activity, ParcoursDoctoral
from parcours_doctoral.utils.formatting import format_activity_ects
from parcours_doctoral.utils.trainings import training_categories_stats
from reference.models.country import Country
from reference.models.language import Language

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
    Tab('documents', _('Documents'), 'folder-open'): [
        Tab('documents', _('Documents'), 'folder-open'),
    ],
    # Tab('person', _('Personal data'), 'user'): [
    #     Tab('person', _('Identification'), 'user'),
    #     Tab('coordonnees', _('Contact details'), 'user'),
    # ],
    # Tab('experience', _('Previous experience'), 'list-alt'): [
    #     Tab('curriculum', _('Curriculum')),
    #     Tab('languages', _('Knowledge of languages')),
    # ],
    # Tab('additional-information', _('Additional information'), 'puzzle-piece'): [
    #     Tab('accounting', _('Accounting')),
    # ],
    Tab('doctorate', pgettext_lazy('tab', 'Research'), 'graduation-cap'): [
        Tab('project', pgettext_lazy('tab', 'Research')),
        Tab('funding', pgettext_lazy('tab', 'Funding')),
        Tab('cotutelle', _('Cotutelle')),
        Tab('supervision', _('Supervision')),
    ],
    Tab('confirmation', pgettext_lazy('tab', 'Confirmation'), 'award'): [
        Tab('confirmation', _('Confirmation exam')),
        Tab('extension-request', _('New deadline')),
    ],
    Tab('training', pgettext_lazy('admission', 'Training'), 'book-open-reader'): [
        Tab('doctoral-training', _('PhD training')),
        Tab('complementary-training', _('Complementary training')),
    ],
    Tab('course-enrollment', _('Course unit enrolment'), 'book-open-reader'): [
        Tab('course-enrollment', _('Course unit enrolment')),
        Tab('assessment-enrollment', _('Assessment enrollments')),
    ],
    Tab('defense', pgettext_lazy('doctorate tab', 'Defence'), 'person-chalkboard'): [
        Tab('jury-preparation', pgettext_lazy('admission tab', 'Defence method')),
        Tab('jury', _('Jury composition')),
        Tab('private-defense', _('Private defence')),
        Tab('public-defense', _('Public defence')),
    ],
    Tab('comments', pgettext_lazy('tab', 'Comments'), 'comments'): [
        Tab('comments', pgettext_lazy('tab', 'Comments'), 'comments')
    ],
    Tab('history', pgettext_lazy('tab', 'History'), 'history'): [
        Tab('history-all', _('All history')),
        Tab('history', _('Status changes')),
    ],
    Tab('management', pgettext_lazy('tab', 'Management'), 'gear'): [
        Tab('send-mail', _('Send a mail')),
        # Tab('debug', _('Debug'), 'bug'),
    ],
}


def get_active_parent(tab_tree, tab_name):
    return next(
        (parent for parent, children in tab_tree.items() if any(child.name == tab_name for child in children)),
        None,
    )


@register.simple_tag(takes_context=True)
def default_tab_context(context):
    match = context['request'].resolver_match
    active_tab = context.get('active_tab', match.url_name)
    active_parent = get_active_parent(TAB_TREE, active_tab)

    if len(match.namespaces) > 1 and match.namespaces[1] != 'update':
        active_tab = match.namespaces[1]

    return {
        'active_parent': active_parent,
        'active_tab': active_tab,
        'parcours_doctoral_uuid': context['view'].kwargs.get('uuid', ''),
        'namespace': ':'.join(match.namespaces[:2]),
        'request': context['request'],
        'view': context['view'],
    }


def get_valid_tab_tree(context, permission_obj, tab_tree):
    """
    Return a tab tree based on the specified one but whose tabs depending on the permissions.
    """
    valid_tab_tree = {}

    # Loop over the tabs of the original tab tree
    for parent_tab, sub_tabs in tab_tree.items():
        # Get the accessible sub tabs depending on the user permissions
        valid_sub_tabs = [tab for tab in sub_tabs if can_read_tab(context, tab.name, permission_obj)]

        # Only add the parent tab if at least one sub tab is allowed
        if len(valid_sub_tabs) > 0:
            valid_tab_tree[parent_tab] = valid_sub_tabs

    return valid_tab_tree


@register.inclusion_tag('parcours_doctoral/includes/parcours_doctoral_tabs_bar.html', takes_context=True)
def parcours_doctoral_tabs(context):
    tab_context = default_tab_context(context)
    parcours_doctoral = context['view'].get_permission_object()
    current_tab_tree = get_valid_tab_tree(context, parcours_doctoral, TAB_TREE).copy()
    tab_context['tab_tree'] = current_tab_tree
    tab_context['tab_badges'] = context.get('tab_badges', {})
    return tab_context


@register.inclusion_tag('parcours_doctoral/includes/subtabs_bar.html', takes_context=True)
def subtabs_bar(context):
    return current_subtabs(context)


@register.simple_tag(takes_context=True)
def current_subtabs(context):
    tab_context = default_tab_context(context)
    permission_obj = context['view'].get_permission_object()
    tab_context['subtabs'] = (
        [tab for tab in TAB_TREE[tab_context['active_parent']] if can_read_tab(context, tab.name, permission_obj)]
        if tab_context['active_parent']
        else []
    )
    return tab_context


@register.simple_tag(takes_context=True)
def has_perm(context, perm, obj=None):
    if not obj:
        obj = context['view'].get_permission_object()
    return context['request'].user.has_perm(perm, obj)


@register.simple_tag(takes_context=True)
def can_read_tab(context, tab_name, obj=None):
    """Return true if the specified tab can be opened in reading mode for this parcours_doctoral, otherwise return False"""
    return has_perm(context, READ_ACTIONS_BY_TAB[tab_name], obj)


@register.simple_tag(takes_context=True)
def can_update_tab(context, tab_name, obj=None):
    """Return true if the specified tab can be opened in update mode for this parcours_doctoral, otherwise return False"""
    return has_perm(context, UPDATE_ACTIONS_BY_TAB[tab_name], obj)


@register.simple_tag(takes_context=True)
def detail_tab_path_from_update(context, parcours_doctoral_uuid):
    """From an update page, get the path of the detail page."""
    match = context['request'].resolver_match
    current_tab_name = context.get('active_tab', match.url_name)
    if len(match.namespaces) > 1 and match.namespaces[1] != 'update':
        current_tab_name = match.namespaces[1]
    return reverse(
        '{}:{}'.format(':'.join(match.namespaces[:-1]), current_tab_name),
        args=[parcours_doctoral_uuid],
    )


@register.simple_tag(takes_context=True)
def update_tab_path_from_detail(context, parcours_doctoral_uuid):
    """From a detail page, get the path of the update page."""
    match = context['request'].resolver_match
    current_tab_name = context.get('active_tab', match.url_name)
    try:
        return reverse(
            '{}:update:{}'.format(':'.join(match.namespaces), current_tab_name),
            args=[parcours_doctoral_uuid],
        )
    except NoReverseMatch:
        if len(match.namespaces) > 1:
            path = ':'.join(match.namespaces[:2])
        else:
            path = '{}:{}'.format(':'.join(match.namespaces), current_tab_name)
        return reverse(
            path,
            args=[parcours_doctoral_uuid],
        )


@register.filter
def status_list(parcours_doctoral):
    statuses = {str(parcours_doctoral.status)}
    for child in parcours_doctoral.children.all():
        statuses.add(str(child.status))
    return ','.join(statuses)


@register.filter
def status_as_class(activity):
    status = activity
    if hasattr(activity, 'status'):
        status = activity.status
    elif isinstance(activity, dict):
        status = activity['status']
    return {
        StatutActivite.SOUMISE.name: "warning",
        StatutActivite.ACCEPTEE.name: "success",
        StatutActivite.REFUSEE.name: "danger",
    }.get(str(status), 'info')


@register.inclusion_tag('parcours_doctoral/includes/training_categories.html')
def training_categories(activities):
    added, validated, categories = training_categories_stats(activities)
    if not added:
        return {}
    return {
        'display_table': any(cat_added + cat_validated for cat_added, cat_validated in categories.values()),
        'categories': categories,
        'added': added,
        'validated': validated,
    }


@register.inclusion_tag('parcours_doctoral/includes/training_categories_credits_table.html')
def training_categories_credits_table(parcours_doctoral_uuid):
    activities = Activity.objects.for_doctoral_training(parcours_doctoral_uuid)
    added, _, categories = training_categories_stats(activities)
    if not added:
        return {}
    return {
        'categories': categories,
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

    return mark_safe(
        ' | '.join(
            f'<strong>{campus_name}</strong>' if getattr(campus, 'uuid', None) in campuses[campus_name] else campus_name
            for campus_name in campuses
        )
    )


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
            template_string = (
                "{% load osis_document_components %}{% document_visualizer files wanted_post_process='ORIGINAL' %}"
            )
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


@register.inclusion_tag('parcours_doctoral/includes/sortable_header_div.html', takes_context=True)
def sortable_header_div(context, order_field_name, order_field_label):
    # Ascending sorting by default
    asc_ordering = True
    ordering_class = 'sort'

    query_params = getattr(context.get('view'), 'query_params', None) or context.request.GET

    query_order_param = query_params.get('o')

    # An order query parameter is already specified
    if query_order_param:
        current_order = query_order_param[0]
        current_order_field = query_order_param.lstrip('-')

        # The current field is already used to sort
        if order_field_name == current_order_field:
            if current_order == '-':
                ordering_class = 'sort-down'
            else:
                asc_ordering = False
                ordering_class = 'sort-up'

    new_params = query_params.copy()
    new_params['o'] = '{}{}'.format('' if asc_ordering else '-', order_field_name)
    new_params.pop('page', None)
    return {
        'field_label': order_field_label,
        'url': context.request.path + '?' + new_params.urlencode(),
        'ordering_class': ordering_class,
    }


@register.filter
def formatted_reference(parcours_doctoral: ParcoursDoctoral):
    return formater_reference(
        reference=parcours_doctoral.reference,
        nom_campus_inscription=parcours_doctoral.training.enrollment_campus.name,
        sigle_entite_gestion=parcours_doctoral.training_management_faculty
        or parcours_doctoral.sigle_entite_gestion,  # From annotation
        annee=parcours_doctoral.training.academic_year.year,
    )


@register.filter
def formatted_language(language: str):
    return language[:2].upper() if language else ''


# TODO Move to osis_document?
@register.simple_tag
def get_image_file_url(file_uuids):
    """Returns the url of the file whose uuid is the first of the specified ones, if it is an image."""
    if file_uuids:
        token = get_remote_token(
            file_uuids[0],
            wanted_post_process=PostProcessingWanted.ORIGINAL.name,
            for_modified_upload=True,
        )
        if token:
            metadata = get_remote_metadata(token)
            if metadata and metadata.get('mimetype') in IMAGE_MIME_TYPES:
                return metadata.get('url')
    return ''


@register.filter
def osis_language_name(code):
    if not code:
        return ''
    try:
        language = Language.objects.get(code=code)
    except Language.DoesNotExist:
        return code
    if get_language() == settings.LANGUAGE_CODE_FR:
        return language.name
    else:
        return language.name_en


@register.inclusion_tag('parcours_doctoral/includes/bootstrap_field_with_tooltip.html')
def bootstrap_field_with_tooltip(field, classes='', show_help=False, html_tooltip=False, label=None, label_class=''):
    return {
        'field': field,
        'classes': classes,
        'show_help': show_help,
        'html_tooltip': html_tooltip,
        'label': label,
        'label_class': label_class,
    }


class FieldWithoutWrapperRenderer(FieldRenderer):
    def render(self):
        return self.get_field_html()


@register.simple_tag
def bootstrap_field_without_wrapper(field):
    return FieldWithoutWrapperRenderer(field).render()


@register.filter(is_safe=False)
def default_if_none_or_empty(value, arg):
    """If value is None or empty, use given default."""
    return value if value not in EMPTY_VALUES else arg


@register.filter()
def format_ects(ects):
    return format_activity_ects(ects=ects)


@register.simple_tag
def get_superior_institute_name(institute_uuid):
    if institute_uuid:
        try:
            return Organization.objects.only('name').get(uuid=institute_uuid).name
        except Organization.DoesNotExist:
            pass
    return ''


@register.simple_tag
def get_thesis_institute_name(institute_uuid):
    if institute_uuid:
        try:
            institute = EntityVersion.objects.only('title', 'acronym').get(uuid=institute_uuid)
            return f'{institute.title} ({institute.acronym})'
        except EntityVersion.DoesNotExist:
            pass
    return ''


@register.filter
def superior_institute_name(organization_uuid):
    if not organization_uuid:
        return ''
    institute = (
        get_superior_institute_queryset().filter(organization_uuid=organization_uuid).order_by('-start_date').first()
    )
    if not institute:
        return organization_uuid
    return mark_safe(format_school_title(institute))


@register.simple_tag(takes_context=True)
def edit_external_member_form(context, membre):
    """Get an edit form"""
    initial = attr.asdict(membre)
    initial['pays'] = initial['code_pays']
    return MemberSupervisionForm(
        prefix=f"member-{membre.uuid}",
        initial=initial,
    )


@register.simple_tag
def url_params_from_form(form):
    """From a django form, return the form data as url request params"""
    url_params = ''

    if form.is_valid():
        for field_name, field_value in form.cleaned_data.items():
            if not field_value:
                continue
            if isinstance(field_value, (list, tuple, set, dict, QuerySet)):
                for sub_value in field_value:
                    url_params += f'&{field_name}={sub_value}'
            else:
                url_params += f'&{field_name}={field_value}'

    return url_params


@register.inclusion_tag('parcours_doctoral/document/dummy.html')
def document_component(document_write_token, document_metadata, can_edit=True):
    """Display the right editor component depending on the file type."""
    if document_metadata:
        if document_metadata.get('mimetype') == PDF_MIME_TYPE:
            attrs = {}
            if not can_edit:
                attrs = {action: False for action in ['comment', 'highlight', 'rotation']}
            return {
                'template': 'osis_document_components/editor.html',
                'value': document_write_token,
                'base_url': settings.OSIS_DOCUMENT_BASE_URL,
                'attrs': attrs,
            }
        elif document_metadata.get('mimetype') in IMAGE_MIME_TYPES:
            return {
                'template': 'parcours_doctoral/document/image.html',
                'url': document_metadata.get('url'),
                'alt': document_metadata.get('name'),
            }
    return {
        'template': 'parcours_doctoral/document/no_document.html',
        'message': _('Non-retrievable document') if document_write_token else _('No document'),
    }


@register.filter
def country_name_from_iso_code(iso_code: str):
    """Return the country name from an iso code."""
    if not iso_code:
        return ''
    country = Country.objects.filter(iso_code=iso_code).values('name', 'name_en').first()
    if not country:
        return ''
    if get_language() == settings.LANGUAGE_CODE_FR:
        return country['name']
    return country['name_en']


@register.simple_tag
def get_confirmation_status(parcours_doctoral: ParcoursDoctoralDTO):
    if (
        ChoixStatutParcoursDoctoral[parcours_doctoral.statut]
        in STATUTS_PAR_ETAPE_PARCOURS_DOCTORAL[ChoixEtapeParcoursDoctoral.CONFIRMATION]
    ):
        return ChoixStatutParcoursDoctoral[parcours_doctoral.statut].value
    return ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE.value


@register.simple_tag(takes_context=True)
def are_jury_member_actions_available(context, membre: MembreJuryDTO):
    can_reset_signatures = context['request'].user.has_perm(
        'parcours_doctoral.jury_reset_signatures', context['view'].get_permission_object()
    )
    return (
        (not membre.est_promoteur and membre.role != 'VERIFICATEUR' and membre.role != 'CDD' and membre.role != 'ADRE')
        or (can_reset_signatures and membre.signature.etat == 'INVITED')
        or (membre.role == 'PRESIDENT' or membre.role == 'SECRETAIRE' or membre.role == 'MEMBRE')
    )
