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
import attr
from django import forms
from django.http import Http404
from django.shortcuts import redirect, resolve_url
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import FormView

from base.views.common import display_error_messages
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import PermissionRequiredMixin
from parcours_doctoral.ddd.commands import (
    ApprouverMembreParPdfCommand,
    DesignerPromoteurReferenceCommand,
    GetGroupeDeSupervisionQuery,
    IdentifierMembreCACommand,
    IdentifierPromoteurCommand,
    ModifierMembreSupervisionExterneCommand,
    SupprimerMembreCACommand,
    SupprimerPromoteurCommand,
)
from parcours_doctoral.forms.supervision import (
    ACTOR_EXTERNAL,
    EXTERNAL_FIELDS,
    ApprovalByPdfForm,
    MemberSupervisionForm,
    SupervisionForm,
)
from parcours_doctoral.models import ActorType
from parcours_doctoral.utils.cache import get_cached_parcours_doctoral_perm_obj
from parcours_doctoral.views.mixins import (
    BusinessExceptionFormViewMixin,
    ParcoursDoctoralViewMixin,
)
from reference.models.country import Country

__namespace__ = None

__all__ = [
    "AddActorFormView",
    "RemoveActorFormView",
    "EditExternalMemberFormView",
    "SetReferencePromoterFormView",
    "ApprovalByPdfFormView",
]


class AddActorFormView(ParcoursDoctoralViewMixin, BusinessExceptionFormViewMixin, FormView):
    urlpatterns = {'supervision': 'supervision'}
    form_class = SupervisionForm
    template_name = 'parcours_doctoral/details/supervision.html'

    def get_permission_required(self):
        if self.request.method == 'GET':
            return ('parcours_doctoral.view_supervision',)
        return ('parcours_doctoral.add_supervision_member',)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groupe_supervision'] = message_bus_instance.invoke(
            GetGroupeDeSupervisionQuery(uuid_parcours_doctoral=self.parcours_doctoral_uuid)
        )
        context['approve_by_pdf_form'] = ApprovalByPdfForm()
        context['add_form'] = context.pop('form')  # Trick template to not add button
        return context

    def prepare_data(self, data):
        is_external = data.pop('internal_external') == ACTOR_EXTERNAL
        person = data.pop('person')
        if not is_external:
            matricule = person
            # Remove data about external actor
            data = {**data, **{f: '' for f in EXTERNAL_FIELDS}}
        else:
            matricule = ''
        pays = data.get('pays')
        if pays:
            data['pays'] = Country.objects.filter(pk=pays).values('iso_code').first()
            if data['pays'] is not None:
                data['pays'] = data['pays']['iso_code']
        return {
            'matricule_auteur': self.request.user.person.global_id,
            'type': data['type'],
            'matricule': matricule,
            **data,
        }

    def call_command(self, form):
        data = self.prepare_data(form.cleaned_data)
        if data.pop('type') == ActorType.CA_MEMBER.name:
            command = IdentifierMembreCACommand
        else:
            command = IdentifierPromoteurCommand

        message_bus_instance.invoke(
            command(
                uuid_parcours_doctoral=self.parcours_doctoral_uuid,
                **data,
            )
        )

    def get_success_url(self):
        return resolve_url('parcours_doctoral:supervision', uuid=self.kwargs['uuid'])


class RemoveActorFormView(ParcoursDoctoralViewMixin, BusinessExceptionFormViewMixin, FormView):
    urlpatterns = {'remove-actor': 'supervision/remove-member/<type>/<uuid_membre>'}
    form_class = forms.Form
    permission_required = 'parcours_doctoral.remove_supervision_member'
    template_name = 'parcours_doctoral/forms/supervision/remove_actor.html'
    actor_type_mapping = {
        ActorType.PROMOTER.name: ('signatures_promoteurs', 'promoteur'),
        ActorType.CA_MEMBER.name: ('signatures_membres_CA', 'membre_CA'),
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            supervision = message_bus_instance.invoke(
                GetGroupeDeSupervisionQuery(uuid_parcours_doctoral=self.kwargs['uuid'])
            )
            supervision = attr.asdict(supervision)
            context['member'] = self.get_member(supervision)
        except (AttributeError, KeyError):
            raise Http404(_('Member not found'))
        return context

    def get_member(self, supervision):
        collection_name, attr_name = self.actor_type_mapping[self.kwargs['type']]
        for signature in supervision[collection_name]:
            member = signature[attr_name]
            if member['uuid'] == self.kwargs['uuid_membre']:
                return member
        raise KeyError

    def prepare_data(self, data):
        return {
            'uuid_parcours_doctoral': self.kwargs['uuid'],
            'matricule_auteur': self.request.user.person.global_id,
        }

    def call_command(self, form):
        data = self.prepare_data(form.cleaned_data)
        if self.kwargs['type'] == ActorType.CA_MEMBER.name:
            data['uuid_membre_ca'] = self.kwargs['uuid_membre']
            command = SupprimerMembreCACommand
        else:
            data['uuid_promoteur'] = self.kwargs['uuid_membre']
            command = SupprimerPromoteurCommand
        message_bus_instance.invoke(command(**data))

    def get_success_url(self):
        return resolve_url('parcours_doctoral:supervision', uuid=self.kwargs['uuid'])


class EditExternalMemberFormView(PermissionRequiredMixin, BusinessExceptionFormViewMixin, FormView):
    urlpatterns = {'edit-external-member': 'edit-external-member/<uuid_membre>'}
    form_class = MemberSupervisionForm
    permission_required = 'parcours_doctoral.edit_external_supervision_member'

    def get_permission_object(self):
        return get_cached_parcours_doctoral_perm_obj(self.kwargs.get('uuid'))

    def get(self, request, *args, **kwargs):
        return redirect('parcours_doctoral:supervision', uuid=self.kwargs['uuid'])

    def prepare_data(self, data):
        return {'uuid_parcours_doctoral': self.kwargs['uuid'], 'uuid_membre': self.kwargs['uuid_membre'], **data}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['prefix'] = f"member-{self.kwargs['uuid_membre']}"
        return kwargs

    def call_command(self, form):
        data = self.prepare_data(form.cleaned_data)
        message_bus_instance.invoke(
            ModifierMembreSupervisionExterneCommand(matricule_auteur=self.request.user.person.global_id, **data)
        )

    def get_success_url(self):
        return resolve_url('parcours_doctoral:supervision', uuid=self.kwargs['uuid'])

    def form_invalid(self, form):
        display_error_messages(
            self.request,
            (
                _("Please correct the errors below"),
                str(form.errors),
            ),
        )
        return redirect('parcours_doctoral:supervision', uuid=self.kwargs['uuid'])


class SetReferencePromoterFormView(PermissionRequiredMixin, BusinessExceptionFormViewMixin, FormView):
    urlpatterns = {'set-reference-promoter': 'set-reference-promoter/<uuid_promoteur>'}
    form_class = forms.Form
    permission_required = 'parcours_doctoral.add_supervision_member'

    def get_permission_object(self):
        return get_cached_parcours_doctoral_perm_obj(self.kwargs.get('uuid'))

    def get(self, request, *args, **kwargs):
        return redirect('parcours_doctoral:supervision', uuid=self.kwargs['uuid'])

    def prepare_data(self, data):
        return {
            'uuid_parcours_doctoral': str(self.kwargs['uuid']),
            'uuid_promoteur': self.kwargs['uuid_promoteur'],
        }

    def call_command(self, form):
        data = self.prepare_data(form.cleaned_data)
        message_bus_instance.invoke(
            DesignerPromoteurReferenceCommand(
                matricule_auteur=self.request.user.person.global_id,
                **data,
            )
        )

    def get_success_url(self):
        return resolve_url('parcours_doctoral:supervision', uuid=self.kwargs['uuid'])

    def form_invalid(self, form):
        return redirect('parcours_doctoral:supervision', uuid=self.kwargs['uuid'])


class ApprovalByPdfFormView(PermissionRequiredMixin, BusinessExceptionFormViewMixin, FormView):
    urlpatterns = 'approve-by-pdf'
    form_class = ApprovalByPdfForm
    permission_required = 'parcours_doctoral.approve_member_by_pdf'

    def get_permission_object(self):
        return get_cached_parcours_doctoral_perm_obj(self.kwargs.get('uuid'))

    def get(self, request, *args, **kwargs):
        return redirect('parcours_doctoral:supervision', uuid=self.kwargs['uuid'])

    def call_command(self, form):
        data = form.cleaned_data
        message_bus_instance.invoke(
            ApprouverMembreParPdfCommand(
                uuid_parcours_doctoral=str(self.kwargs["uuid"]),
                matricule_auteur=self.request.user.person.global_id,
                **data,
            )
        )

    def get_success_url(self):
        return resolve_url('parcours_doctoral:supervision', uuid=self.kwargs['uuid'])

    def form_invalid(self, form):
        return redirect('parcours_doctoral:supervision', uuid=self.kwargs['uuid'])
