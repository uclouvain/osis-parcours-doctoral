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

from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from base.auth.roles.program_manager import ProgramManager
from base.forms.utils import autocomplete
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import TrainingType
from base.models.enums.entity_type import EntityType
from parcours_doctoral.ddd.domain.model.enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ENTITY_CDE,
    ENTITY_CDSS,
    ENTITY_CLSM,
    ENTITY_SCIENCES,
    SIGLE_SCIENCES,
)
from parcours_doctoral.models.entity_proxy import EntityProxy

ALL_FEMININE_EMPTY_CHOICE = (('', pgettext_lazy('filters feminine', 'All')),)


class DashboardForm(forms.Form):
    cdds = forms.MultipleChoiceField(
        label=_('Doctoral commissions'),
        required=False,
        widget=autocomplete.Select2Multiple(),
    )

    commission_proximite = forms.ChoiceField(
        label=_('Proximity commission'),
        required=False,
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.managed_education_groups = ProgramManager.objects.filter(person=user.person).values_list(
            'education_group_id',
            flat=True,
        )

        self.cdd_acronyms = self.get_cdd_queryset()

        self.fields['cdds'].choices = []
        for acronym in self.cdd_acronyms:
            self.fields['cdds'].choices.append((acronym, acronym))

        self.fields['commission_proximite'].choices = self.get_proximity_commission_choices()

    def get_cdd_queryset(self):
        """Used to determine which doctoral commission to filter on"""
        qs = EntityProxy.objects.filter(entityversion__entity_type=EntityType.DOCTORAL_COMMISSION.name)

        if self.managed_education_groups:
            qs = qs.filter(management_entity__education_group_id__in=self.managed_education_groups)

        return (
            qs.with_acronym()
            .distinct('acronym')
            .order_by('acronym')
            .values_list(
                'acronym',
                flat=True,
            )
        )

    def get_proximity_commission_choices(self):
        proximity_commission_choices = [ALL_FEMININE_EMPTY_CHOICE[0]]

        if ENTITY_CDE in self.cdd_acronyms or ENTITY_CLSM in self.cdd_acronyms:
            proximity_commission_choices.append(
                ['{} / {}'.format(ENTITY_CDE, ENTITY_CLSM), ChoixCommissionProximiteCDEouCLSM.choices()]
            )

        if ENTITY_CDSS in self.cdd_acronyms:
            proximity_commission_choices.append([ENTITY_CDSS, ChoixCommissionProximiteCDSS.choices()])

        managed_trainings = EducationGroupYear.objects.filter(education_group_type__name=TrainingType.PHD.name)

        if self.managed_education_groups:
            managed_trainings = managed_trainings.filter(education_group_id__in=self.managed_education_groups)

        if managed_trainings.filter(acronym=SIGLE_SCIENCES).exists():
            proximity_commission_choices.append([ENTITY_SCIENCES, ChoixSousDomaineSciences.choices()])

        return proximity_commission_choices
