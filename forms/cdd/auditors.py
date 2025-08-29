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
from django import forms
from django.forms import formset_factory
from django.utils import timezone
from django.utils.functional import cached_property

from admission.forms import DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS
from base.forms.utils.autocomplete import ModelSelect2
from base.models.entity_version import EntityVersion
from base.models.enums.entity_type import EntityType
from base.models.enums.organization_type import MAIN
from base.models.person import Person
from parcours_doctoral.auth.roles.auditor import Auditor


class AuditorsConfigForm(forms.Form):
    entity_version = forms.ModelChoiceField(
        queryset=EntityVersion.objects.filter(entity__organization__type=MAIN, entity_type=EntityType.INSTITUTE.name),
        disabled=True,
    )
    auditor = forms.ModelChoiceField(
        queryset=Person.objects.filter(student__isnull=True),
        widget=ModelSelect2(
            url='parcours_doctoral:autocomplete:auditors',
            attrs=DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS,
        ),
        required=False,
    )


class AuditorsConfigBaseFormset(forms.BaseFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.entities_versions = list(
            EntityVersion.objects.filter(
                entity__organization__type=MAIN,
                entity_type=EntityType.INSTITUTE.name,
            )
            .prefetch_related('parent__entityversion_set')
            .current(timezone.now())
            .order_by('parent')
        )
        self.auditors = {
            auditor['entity_id']: auditor['person_id']
            for auditor in Auditor.objects.all().values('entity_id', 'person_id')
        }

    @cached_property
    def forms(self):
        """Instantiate forms at first property access."""
        # DoS protection is included in total_form_count()
        return [
            self._construct_form(
                i,
                initial={
                    'entity_version': self.entities_versions[i],
                    'auditor': self.auditors.get(self.entities_versions[i].entity_id),
                },
            )
            for i in range(self.total_form_count())
        ]

    def initial_form_count(self):
        return len(self.entities_versions)

    def total_form_count(self):
        return len(self.entities_versions)


AuditorsConfigFormset = formset_factory(
    AuditorsConfigForm,
    formset=AuditorsConfigBaseFormset,
    extra=0,
    validate_max=True,
    validate_min=True,
)
