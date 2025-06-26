# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from osis_role.contrib.views import PermissionRequiredMixin
from parcours_doctoral.auth.roles.auditor import Auditor
from parcours_doctoral.forms.cdd.auditors import AuditorsConfigFormset

__all__ = [
    'AuditorsConfigView',
]


class AuditorsConfigView(PermissionRequiredMixin, SuccessMessageMixin, FormView):
    urlpatterns = {'auditors': 'auditors'}
    template_name = 'parcours_doctoral/config/auditors.html'
    permission_required = 'parcours_doctoral.change_auditors_configuration'
    form_class = AuditorsConfigFormset
    success_message = _("Configuration saved.")
    success_url = reverse_lazy("parcours_doctoral:config:auditors")

    @transaction.atomic
    def form_valid(self, formset):
        auditors = [
            Auditor(entity_id=form.cleaned_data['entity_version'].entity_id, person=form.cleaned_data['auditor'])
            for form in formset
            if form.cleaned_data['auditor']
        ]
        Auditor.objects.bulk_create(
            auditors,
            update_conflicts=True,
            update_fields=['person'],
            unique_fields=['entity'],
        )
        auditors_entities_to_be_deleted = [
            form.cleaned_data['entity_version'].entity_id for form in formset if not form.cleaned_data['auditor']
        ]
        Auditor.objects.filter(entity_id__in=auditors_entities_to_be_deleted).delete()
        return super().form_valid(formset)
