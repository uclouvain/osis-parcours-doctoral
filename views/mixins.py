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
import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import resolve_url
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import ContextMixin

from admission.utils import add_messages_into_htmx_response, add_close_modal_into_htmx_response
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from infrastructure.messages_bus import message_bus_instance
from osis_common.ddd.interface import BusinessException
from osis_role.contrib.views import PermissionRequiredMixin
from parcours_doctoral.ddd.commands import RecupererParcoursDoctoralQuery
from parcours_doctoral.ddd.dtos import ParcoursDoctoralDTO
from parcours_doctoral.models.parcours_doctoral import ParcoursDoctoral
from parcours_doctoral.utils import get_cached_parcours_doctoral_perm_obj


class ParcoursDoctoralViewMixin(LoginRequiredMixin, PermissionRequiredMixin, ContextMixin):
    @property
    def parcours_doctoral_uuid(self) -> str:
        return self.kwargs.get('uuid', '')

    @property
    def parcours_doctoral(self) -> ParcoursDoctoral:
        return get_cached_parcours_doctoral_perm_obj(self.parcours_doctoral_uuid)

    def get_permission_object(self):
        return self.parcours_doctoral

    @cached_property
    def parcours_doctoral_dto(self) -> ParcoursDoctoralDTO:
        return message_bus_instance.invoke(RecupererParcoursDoctoralQuery(
            parcours_doctoral_uuid=self.parcours_doctoral_uuid,
        ))

    @cached_property
    def next_url(self):
        url = self.request.GET.get('next', '')
        hash_url = self.request.GET.get('next_hash_url', '')
        return f'{url}#{hash_url}' if hash_url else url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['original_parcours_doctoral'] = self.parcours_doctoral
        context['next_url'] = self.next_url

        # TODO À faire dans parcours doctoral ?
        # # Get the next and previous parcours_doctorals from the last computed listing
        # cached_parcours_doctorals_list = cache.get(BaseAdmissionList.cache_key_for_result(user_id=self.request.user.id))
        #
        # if cached_parcours_doctorals_list and self.parcours_doctoral_uuid in cached_parcours_doctorals_list:
        #     current_parcours_doctoral = cached_parcours_doctorals_list[self.parcours_doctoral_uuid]
        #     for key in ['previous', 'next']:
        #         if current_parcours_doctoral[key]:
        #             context[f'{key}_parcours_doctoral_url'] = resolve_url('parcours_doctoral:base', uuid=current_parcours_doctoral[key])

        context['parcours_doctoral'] = self.parcours_doctoral_dto
        return context


class ParcoursDoctoralFormMixin(ParcoursDoctoralViewMixin):
    message_on_success = _('Your data have been saved.')
    message_on_failure = _('Some errors have been encountered.')
    default_htmx_trigger_form_extra = {}
    close_modal_on_htmx_request = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_headers = {}
        self.htmx_refresh = False
        self.htmx_trigger_form_extra = {**self.default_htmx_trigger_form_extra}

    def htmx_trigger_form(self, is_valid: bool):
        """Add a JS event to listen for when the form is submitted through HTMX."""
        self.custom_headers = {
            'HX-Trigger': {
                "formValidation": {
                    "is_valid": is_valid,
                    "message": str(self.message_on_success if is_valid else self.message_on_failure),
                    **self.htmx_trigger_form_extra,
                }
            }
        }

    def update_current_parcours_doctoral_on_form_valid(self, form, parcours_doctoral):
        """Override this method to update the current parcours_doctoral on form valid."""
        pass

    def form_valid(self, form):
        messages.success(self.request, str(self.message_on_success))

        if self.request.htmx:
            self.htmx_trigger_form(is_valid=True)
            response = self.render_to_response(self.get_context_data(form=form))
            if self.htmx_refresh:
                response.headers['HX-Refresh'] = 'true'
            else:
                add_messages_into_htmx_response(request=self.request, response=response)
                if self.close_modal_on_htmx_request:
                    add_close_modal_into_htmx_response(response=response)
            return response

        return super().form_valid(form)

    def get_checklist_redirect_url(self):
        # If specified, return to the correct checklist tab
        if 'next' in self.request.GET:
            url = resolve_url(f'parcours_doctoral:{self.current_context}:checklist', uuid=self.parcours_doctoral_uuid)
            return f"{url}#{self.request.GET['next']}"

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        # Add custom headers
        for header_key, header_value in self.custom_headers.items():
            current_data_str = response.headers.get(header_key)
            if current_data_str:
                current_data = json.loads(current_data_str)
                current_data.update(header_value)
            else:
                current_data = header_value
            response.headers[header_key] = json.dumps(current_data)
        return response

    def form_invalid(self, form):
        messages.error(self.request, str(self.message_on_failure))
        response = super().form_invalid(form)
        if self.request.htmx:
            self.htmx_trigger_form(is_valid=False)
            add_messages_into_htmx_response(request=self.request, response=response)
        return response


class LastConfirmationMixin(ParcoursDoctoralViewMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) if hasattr(super(), 'get_context_data') else {}
        context['confirmation_paper'] = self.last_confirmation_paper
        return context


class BusinessExceptionFormViewMixin:
    error_mapping = {}

    def __init__(self, *args, **kwargs):
        self._error_mapping = {exc.status_code: field for exc, field in self.error_mapping.items()}
        super().__init__(*args, **kwargs)

    def call_command(self, form):
        raise NotImplementedError

    def form_valid(self, form):
        try:
            self.call_command(form=form)
        except MultipleBusinessExceptions as multiple_exceptions:
            for exception in multiple_exceptions.exceptions:
                status_code = getattr(exception, 'status_code', None)
                form.add_error(self._error_mapping.get(status_code), exception.message)
            return self.form_invalid(form=form)
        except BusinessException as exception:
            messages.error(self.request, _("Some errors have been encountered."))
            status_code = getattr(exception, 'status_code', None)
            form.add_error(self._error_mapping.get(status_code), exception.message)
            return self.form_invalid(form=form)

        return super().form_valid(form=form)
