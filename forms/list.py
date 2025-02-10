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
import re

from dal import forward
from django import forms
from django.conf import settings
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixTypeAdmission,
)
from admission.forms import DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS
from admission.models.enums.actor_type import ActorType
from base.auth.roles.program_manager import ProgramManager
from base.forms.utils import autocomplete
from base.forms.utils.datefield import DatePickerInput
from base.forms.widgets import Select2MultipleCheckboxesWidget
from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import TrainingType
from base.models.enums.entity_type import EntityType
from base.models.person import Person
from base.templatetags.pagination_bs5 import DEFAULT_PAGINATOR_SIZE, PAGINATOR_SIZE_LIST
from education_group.templatetags.education_group_extra import format_to_academic_year
from parcours_doctoral.ddd.domain.model.enums import (
    STATUTS_ACTIFS,
    STATUTS_INACTIFS,
    STATUTS_PAR_ETAPE_PARCOURS_DOCTORAL,
    BourseRecherche,
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixEtapeParcoursDoctoral,
    ChoixSousDomaineSciences,
    ChoixTypeFinancement,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ENTITY_CDE,
    ENTITY_CDSS,
    ENTITY_CLSM,
    ENTITY_SCIENCES,
    SIGLE_SCIENCES,
)
from parcours_doctoral.ddd.jury.domain.model.enums import RoleJury
from parcours_doctoral.models import JuryMember, ParcoursDoctoralSupervisionActor
from parcours_doctoral.models.entity_proxy import EntityProxy
from reference.models.enums.scholarship_type import ScholarshipType
from reference.models.scholarship import Scholarship

REGEX_REFERENCE = r'\d{4}\.\d{4}$'
ALL_EMPTY_CHOICE = (('', pgettext_lazy('filters', 'All')),)
ALL_FEMININE_EMPTY_CHOICE = (('', pgettext_lazy('filters feminine', 'All')),)


class ParcoursDoctorauxFilterForm(forms.Form):
    annee_academique = forms.TypedChoiceField(
        label=_('Year'),
        coerce=int,
    )

    numero = forms.RegexField(
        label=_('Application numero'),
        regex=re.compile(REGEX_REFERENCE),
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'L-ESPO22-0001.2345',
            },
        ),
    )

    matricule_doctorant = forms.CharField(
        label=_('Last name / First name / NOMA'),
        required=False,
        widget=autocomplete.ListSelect2(
            url="parcours_doctoral:autocomplete:students",
            attrs=DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS,
        ),
    )

    uuid_promoteur = forms.CharField(
        label=pgettext_lazy('gender', 'Supervisor'),
        required=False,
        widget=autocomplete.ListSelect2(
            url="parcours_doctoral:autocomplete:supervision-actors",
            attrs={
                **DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS,
                'data-placeholder': _('Last name / First name / Global id'),
            },
            forward=[
                forward.Const(ActorType.PROMOTER.name, "actor_type"),
            ],
        ),
    )

    uuid_president_jury = forms.CharField(
        label=_('Jury chair'),
        required=False,
        widget=autocomplete.ListSelect2(
            url="parcours_doctoral:autocomplete:jury-members",
            attrs={
                **DEFAULT_AUTOCOMPLETE_WIDGET_ATTRS,
                'data-placeholder': _('Last name / First name / Global id'),
            },
            forward=[
                forward.Const(RoleJury.PRESIDENT.name, "role"),
            ],
        ),
    )

    type_admission = forms.ChoiceField(
        choices=ALL_EMPTY_CHOICE + ChoixTypeAdmission.choices(),
        label=pgettext_lazy('doctorate-filter', 'Admission type'),
        required=False,
    )

    type_financement = forms.ChoiceField(
        choices=ALL_EMPTY_CHOICE + ChoixTypeFinancement.choices(),
        label=_('Funding type'),
        required=False,
    )

    bourse_recherche = forms.ChoiceField(
        label=_("Research scholarship"),
        required=False,
    )

    fnrs_fria_fresh = forms.BooleanField(
        label=_("FNRS, FRIA, FRESH"),
        required=False,
    )

    statuts = forms.MultipleChoiceField(
        choices=[
            [step.value, [[status.name, status.value] for status in statuses]]
            for step, statuses in STATUTS_PAR_ETAPE_PARCOURS_DOCTORAL.items()
            if statuses
        ],
        initial=list(STATUTS_ACTIFS),
        label=_('Application status'),
        required=False,
        widget=Select2MultipleCheckboxesWidget(
            attrs={
                'data-dropdown-auto-width': True,
                'data-selection-template': _("{items} types out of {total}"),
            },
            filters=[
                Select2MultipleCheckboxesWidget.Filter(
                    label=_('Select the active statuses'),
                    options_values=STATUTS_ACTIFS,
                ),
                Select2MultipleCheckboxesWidget.Filter(
                    label=_('Select the inactive statuses'),
                    options_values=STATUTS_INACTIFS,
                ),
            ],
        ),
    )

    cdds = forms.MultipleChoiceField(
        label=_('Doctoral commissions'),
        required=False,
        widget=autocomplete.Select2Multiple(),
    )

    commission_proximite = forms.ChoiceField(
        label=_('Proximity commission'),
        required=False,
    )

    sigles_formations = forms.MultipleChoiceField(
        label=pgettext_lazy('doctorate', 'Courses'),
        required=False,
        widget=autocomplete.Select2Multiple(
            attrs={
                'data-placeholder': _('Acronym / Title'),
            },
        ),
    )

    instituts_secteurs = forms.MultipleChoiceField(
        label=_('Institute / Sector'),
        required=False,
        widget=autocomplete.Select2Multiple(),
    )

    taille_page = forms.TypedChoiceField(
        label=_("Page size"),
        choices=((size, size) for size in PAGINATOR_SIZE_LIST),
        widget=forms.Select(attrs={'form': 'search_form', 'autocomplete': 'off'}),
        help_text=_("items per page"),
        required=False,
        initial=DEFAULT_PAGINATOR_SIZE,
        coerce=int,
    )

    page = forms.IntegerField(
        label=_("Page"),
        widget=forms.HiddenInput(),
        required=False,
        initial=1,
    )

    class Media:
        js = [
            # DependsOn
            'js/dependsOn.min.js',
            # Mask
            'js/jquery.mask.min.js',
        ]

    def __init__(self, user, load_labels=False, *args, **kwargs):
        if kwargs.get('data'):
            kwargs['data'] = kwargs['data'].copy()
            kwargs['data'].setdefault('taille_page', DEFAULT_PAGINATOR_SIZE)

        super().__init__(*args, **kwargs)

        self.user = user

        self.managed_education_groups = ProgramManager.objects.filter(
            person=self.user.person,
        ).values_list('education_group_id', flat=True)

        # Initialize the academic year field
        self.fields['annee_academique'].choices = self.get_academic_year_choices()
        current_academic_year = AcademicYear.objects.current()
        if current_academic_year:
            self.fields['annee_academique'].initial = current_academic_year.year

        # Initialize the CDDs field
        self.cdd_acronyms = self.get_cdd_queryset()
        self.fields['cdds'].choices = [(acronym, acronym) for acronym in self.cdd_acronyms]
        # Hide the CDDs field if the user manages only one cdd
        if len(self.cdd_acronyms) <= 1:
            self.fields['cdds'].widget = forms.MultipleHiddenInput()

        # Initialize the program field
        self.doctorates = self.get_doctorate_queryset()
        self.fields['sigles_formations'].choices = [
            (acronym, '{} - {}'.format(acronym, title)) for acronym, title in self.doctorates
        ]

        # Initialize the proximity commission field
        self.fields['commission_proximite'].choices = self.get_proximity_commission_choices()
        # Hide the proximity commission field if there is only one choice
        if len(self.fields['commission_proximite'].choices) == 1:
            self.fields['commission_proximite'].widget = forms.HiddenInput()

        # Initialize the scholarship field
        self.fields['bourse_recherche'].choices = self.get_scholarship_choices()

        # Initialize the institute sector field
        self.sectors_acronyms = set()

        self.fields['instituts_secteurs'].choices = self.get_institute_and_sector_choices()

        # Initialize the labels of the autocomplete fields
        if load_labels:
            student_global_id = self.data.get(self.add_prefix('matricule_doctorant'))
            if student_global_id:
                student = Person.objects.filter(global_id=student_global_id).only('first_name', 'last_name').first()
                if student:
                    self.fields['matricule_doctorant'].widget.choices = [
                        [student_global_id, f'{student.last_name}, {student.first_name}']
                    ]

            promoter_uuid = self.data.get(self.add_prefix('uuid_promoteur'))
            if promoter_uuid:
                promoter = (
                    ParcoursDoctoralSupervisionActor.objects.filter(uuid=promoter_uuid).select_related('person').first()
                )
                if promoter:
                    self.fields['uuid_promoteur'].widget.choices = [
                        [promoter_uuid, promoter.complete_name],
                    ]

            jury_president_uuid = self.data.get(self.add_prefix('uuid_president_jury'))
            if jury_president_uuid:
                jury_president = (
                    JuryMember.objects.filter(uuid=jury_president_uuid)
                    .select_related(
                        'person',
                        'promoter__person',
                    )
                    .first()
                )
                if jury_president:
                    self.fields['uuid_president_jury'].widget.choices = [
                        [jury_president_uuid, jury_president.complete_name]
                    ]

    def get_academic_year_choices(self):
        academic_years = AcademicYear.objects.all().order_by('-year')
        return [(academic_year.year, format_to_academic_year(academic_year.year)) for academic_year in academic_years]

    def get_scholarship_choices(self):
        doctorate_scholarships = Scholarship.objects.filter(
            type=ScholarshipType.BOURSE_INTERNATIONALE_DOCTORAT.name,
        ).order_by('short_name')

        return (
            [ALL_FEMININE_EMPTY_CHOICE[0]]
            + [(scholarship.uuid, scholarship.short_name) for scholarship in doctorate_scholarships]
            + [(BourseRecherche.OTHER.name, BourseRecherche.OTHER.value)]
        )

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

    def get_institute_and_sector_choices(self):
        """Used to determine which institute / sector to filter on"""
        qs = EntityProxy.objects.filter(
            entityversion__entity_type__in=[
                EntityType.INSTITUTE.name,
                EntityType.SECTOR.name,
            ],
        )
        qs = (
            qs.with_acronym()
            .distinct('acronym')
            .order_by('acronym')
            .values(
                'entityversion__entity_type',
                'acronym',
            )
        )

        choices = []

        for row in qs:
            if row['entityversion__entity_type'] == EntityType.SECTOR.name:
                self.sectors_acronyms.add(row['acronym'])

            choices.append((row['acronym'], row['acronym']))

        return choices

    def get_doctorate_queryset(self):
        """Used to determine which training to filter on"""
        qs = EducationGroupYear.objects.filter(education_group_type__name=TrainingType.PHD.name)

        if self.managed_education_groups:
            qs = qs.filter(education_group_id__in=self.managed_education_groups)

        return (
            qs.distinct('acronym')
            .values_list('acronym', 'title' if get_language() == settings.LANGUAGE_CODE_FR else 'title_english')
            .order_by('acronym')
        )

    def get_proximity_commission_choices(self):
        proximity_commission_choices = [ALL_FEMININE_EMPTY_CHOICE[0]]

        if ENTITY_CDE in self.cdd_acronyms or ENTITY_CLSM in self.cdd_acronyms:
            proximity_commission_choices.append(
                ['{} / {}'.format(ENTITY_CDE, ENTITY_CLSM), ChoixCommissionProximiteCDEouCLSM.choices()]
            )

        if ENTITY_CDSS in self.cdd_acronyms:
            proximity_commission_choices.append([ENTITY_CDSS, ChoixCommissionProximiteCDSS.choices()])

        if SIGLE_SCIENCES in dict(self.doctorates):
            proximity_commission_choices.append([ENTITY_SCIENCES, ChoixSousDomaineSciences.choices()])

        return proximity_commission_choices

    def clean_numero(self):
        numero = self.cleaned_data.get('numero')
        return re.search(REGEX_REFERENCE, numero).group(0).replace('.', '') if numero else ''

    def clean_taille_page(self):
        return self.cleaned_data.get('taille_page') or self.fields['taille_page'].initial

    def clean_page(self):
        return self.cleaned_data.get('page') or self.fields['page'].initial

    def clean(self):
        cleaned_data = super().clean()

        sector_institutes_values = cleaned_data.get('instituts_secteurs')

        cleaned_data['instituts'] = []
        cleaned_data['secteurs'] = []

        if sector_institutes_values:
            for value in sector_institutes_values:
                cleaned_data['secteurs' if value in self.sectors_acronyms else 'instituts'].append(value)

        return cleaned_data


class IntervalDateForm(forms.Form):
    type_date = forms.ChoiceField(
        choices=ChoixEtapeParcoursDoctoral.choices_except(ChoixEtapeParcoursDoctoral.JURY),
        label=_('Date type'),
    )

    date_debut = forms.DateField(
        label=_('From'),
        required=False,
        widget=DatePickerInput(),
    )

    date_fin = forms.DateField(
        label=_('To'),
        required=False,
        widget=DatePickerInput(),
    )

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get('date_debut')
        end_date = cleaned_data.get('date_fin')

        if not start_date and not end_date:
            raise forms.ValidationError(_('Please select at least one date.'))

        elif start_date and end_date and start_date > end_date:
            raise forms.ValidationError(_("The start date can't be later than the end date"))

        return cleaned_data


IntervalDateFormSet = forms.formset_factory(IntervalDateForm, extra=0)
