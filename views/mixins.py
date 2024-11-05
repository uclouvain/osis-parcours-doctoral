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
from infrastructure.messages_bus import message_bus_instance
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
        # # Get the next and previous admissions from the last computed listing
        # cached_admissions_list = cache.get(BaseAdmissionList.cache_key_for_result(user_id=self.request.user.id))
        #
        # if cached_admissions_list and self.admission_uuid in cached_admissions_list:
        #     current_admission = cached_admissions_list[self.admission_uuid]
        #     for key in ['previous', 'next']:
        #         if current_admission[key]:
        #             context[f'{key}_admission_url'] = resolve_url('admission:base', uuid=current_admission[key])

        context['parcours_doctoral'] = self.parcours_doctoral_dto
        return context

    def dispatch(self, request, *args, **kwargs):
        # TODO Vérifier si on doit avoir la même chose pour parcours doctoral
        # if (
        #     request.method == 'GET'
        #     and self.admission_uuid
        #     and getattr(request.user, 'person', None)
        #     and (SicManagement.belong_to(request.user.person) or CentralManager.belong_to(request.user.person))
        # ):
        #     AdmissionViewer.add_viewer(person=request.user.person, admission=self.admission)

        return super().dispatch(request, *args, **kwargs)


class ParcoursDoctoralFormMixin(ParcoursDoctoralViewMixin):
    message_on_success = _('Your data have been saved.')
    message_on_failure = _('Some errors have been encountered.')
    update_parcours_doctoral_author = False
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

    def update_current_admission_on_form_valid(self, form, admission):
        """Override this method to update the current admission on form valid."""
        pass

    def form_valid(self, form):
        messages.success(self.request, str(self.message_on_success))

        # Update the last update author of the admission
        author = getattr(self.request.user, 'person')
        if self.update_parcours_doctoral_author and author:
            admission = ParcoursDoctoral.objects.get(uuid=self.parcours_doctoral_uuid)
            admission.last_update_author = author
            # Additional updates if needed
            self.update_current_admission_on_form_valid(form, admission)
            admission.save()

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
            url = resolve_url(f'admission:{self.current_context}:checklist', uuid=self.admission_uuid)
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
