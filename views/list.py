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
import datetime

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.cache import cache
from django.core.exceptions import NON_FIELD_ERRORS
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views.generic import ListView
from django.views.generic.edit import FormMixin

from admission.utils import add_messages_into_htmx_response
from admission.views import ListPaginator
from base.templatetags.pagination_bs5 import DEFAULT_PAGINATOR_SIZE
from base.views.common import display_error_messages
from infrastructure.messages_bus import message_bus_instance
from osis_common.utils.htmx import HtmxMixin
from parcours_doctoral.ddd.read_view.queries import ListerTousParcoursDoctorauxQuery
from parcours_doctoral.forms.list import (
    IntervalDateFormSet,
    ParcoursDoctorauxFilterForm,
)

__all__ = [
    "ParcoursDoctoralList",
]


class ParcoursDoctoralList(LoginRequiredMixin, PermissionRequiredMixin, HtmxMixin, FormMixin, ListView):
    template_name = 'parcours_doctoral/list/list.html'
    htmx_template_name = 'parcours_doctoral/list/list_block.html'
    permission_required = 'parcours_doctoral.view_parcours_doctoral'
    filtering_query_class = ListerTousParcoursDoctorauxQuery
    form_class = ParcoursDoctorauxFilterForm
    urlpatterns = 'list'
    paginator_class = ListPaginator

    raise_exception = True
    parameters_cache_timeout = None
    result_cache_timeout = 60 * 60 * 24  # 1 day

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.form = None
        self.date_formset = None
        self.filters = {}

    @property
    def cache_key(self):
        return f"cache_parcours_doctoral_filter_{self.request.user.id}_{self.request.path}"

    @classmethod
    def cache_key_for_result(cls, user_id):
        return f"cache_parcours_doctoral_filter_result_{user_id}"

    @staticmethod
    def htmx_render_form_errors(request, form, prefix=''):
        """Display the form errors through the django messages."""
        display_error_messages(
            request=request,
            messages_to_display=[
                '{prefix}{field_name}{errors}'.format(
                    prefix=prefix + ' - ' if prefix else '',
                    field_name=form.fields.get(field_name).label + ' - ' if field_name != NON_FIELD_ERRORS else '',
                    errors=' '.join(errors),
                )
                for field_name, errors in form.errors.items()
            ],
        )

    def get_context_data(self, **kwargs):
        kwargs['form'] = self.form
        kwargs['date_formset'] = self.date_formset
        kwargs['filter_form'] = self.form
        kwargs['htmx_template_name'] = self.htmx_template_name
        kwargs['default_form_values'] = {field.id_for_label: field.initial for field in self.form if field.initial}
        kwargs['now'] = datetime.datetime.now()
        return super().get_context_data(**kwargs)

    def get_paginate_by(self, queryset):
        if self.form.is_valid() and self.form.cleaned_data.get('taille_page'):
            return self.form.cleaned_data.get('taille_page')
        return DEFAULT_PAGINATOR_SIZE

    @cached_property
    def query_params(self):
        return self.request.GET or cache.get(self.cache_key)

    def get_form_kwargs(self):
        return {
            'data': self.query_params,
            'load_labels': not self.request.htmx,
            'user': self.request.user,
        }

    def get(self, request, *args, **kwargs):
        self.form = self.get_form()

        self.date_formset = IntervalDateFormSet(
            data=self.query_params,
            prefix='date_form',
        )

        form_is_valid = self.form.is_valid()
        formset_is_valid = self.date_formset.is_valid()

        if not form_is_valid or not formset_is_valid:
            self.object_list = []
            response = self.form_invalid(form=self.form)

            if not form_is_valid:
                self.htmx_render_form_errors(self.request, self.form)
            if not formset_is_valid:
                for index, date_form in enumerate(self.date_formset, start=1):
                    if not date_form.is_valid():
                        self.htmx_render_form_errors(
                            self.request,
                            date_form,
                            prefix=_('Date - Filter #%s') % index,
                        )

            if self.request.htmx:
                add_messages_into_htmx_response(request=self.request, response=response)

            return response

        if self.request.GET:
            cache.set(self.cache_key, self.request.GET, timeout=self.parameters_cache_timeout)

        self.filters = self.form.cleaned_data
        self.filters.pop('instituts_secteurs', None)

        self.filters['dates'] = []
        for date_form in self.date_formset:
            cleaned_data = date_form.cleaned_data
            self.filters['dates'].append(
                (
                    cleaned_data['type_date'],
                    cleaned_data['date_debut'],
                    cleaned_data['date_fin'],
                ),
            )

        if self.query_params:
            # Add page number to kwargs to pass it to the paginator
            self.kwargs['page'] = self.query_params.get('page')

            # Order the queryset if specified
            ordering_field = self.query_params.get('o')

            if ordering_field:
                self.filters['tri_inverse'] = ordering_field[0] == '-'
                self.filters['champ_tri'] = ordering_field.lstrip('-')

        response = super().get(request, *args, **kwargs)

        if self.request.GET:
            cache.set(
                self.cache_key_for_result(user_id=self.request.user.id),
                self.object_list.sorted_elements,
                timeout=self.result_cache_timeout,
            )

        return response

    def get_queryset(self):
        return message_bus_instance.invoke(
            self.filtering_query_class(
                **self.filters,
                demandeur=self.request.user.person.uuid,
            )
        )
