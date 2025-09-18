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
import datetime
from functools import partial
from typing import List, Optional, Tuple

from dal.forward import Field
from django import forms
from django.utils.dates import MONTHS_ALT
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from base.forms.utils import EMPTY_CHOICE, autocomplete
from base.forms.utils.academic_year_field import AcademicYearModelChoiceField
from base.forms.utils.datefield import DatePickerInput
from base.models.academic_year import AcademicYear, current_academic_year
from base.models.learning_unit_year import LearningUnitYear
from deliberation.models.enums.numero_session import Session
from parcours_doctoral.constants import INSTITUTION_UCL
from parcours_doctoral.ddd.formation.domain.model.enums import (
    CategorieActivite,
    ChoixComiteSelection,
    ChoixTypeEpreuve,
    ContexteFormation,
)
from parcours_doctoral.forms.fields import SelectOrOtherField
from parcours_doctoral.models import AssessmentEnrollment
from parcours_doctoral.models.activity import Activity
from parcours_doctoral.models.cdd_config import CddConfiguration

__all__ = [
    "ConfigurableActivityTypeField",
    "ConferenceForm",
    "ConferenceCommunicationForm",
    "ConferencePublicationForm",
    "CommunicationForm",
    "PublicationForm",
    "ResidencyForm",
    "ResidencyCommunicationForm",
    "ServiceForm",
    "SeminarForm",
    "SeminarCommunicationForm",
    "ValorisationForm",
    "CourseForm",
    "PaperForm",
    "ComplementaryCourseForm",
    "UclCourseForm",
    "UclCompletedCourseForm",
    "get_category_labels",
]

from parcours_doctoral.models.parcours_doctoral import ParcoursDoctoral

MINIMUM_YEAR = 2000


def year_choices():
    return [EMPTY_CHOICE[0]] + [(int(year), year) for year in range(datetime.date.today().year, MINIMUM_YEAR, -1)]


def month_choices():
    return [EMPTY_CHOICE[0]] + [(int(index), month) for index, month in MONTHS_ALT.items()]


def get_cdd_config(cdd_id) -> CddConfiguration:
    return CddConfiguration.objects.get_or_create(cdd_id=cdd_id)[0]


def get_category_labels(cdd_id, lang_code: str = None) -> List[Tuple[str, str]]:
    lang_code = lang_code or get_language()
    original_constants = dict(CategorieActivite.choices()).keys()
    return [
        (constant, label)
        for constant, label in zip(original_constants, get_cdd_config(cdd_id).category_labels[lang_code])
        if constant != CategorieActivite.UCL_COURSE.name
    ]


class ConfigurableActivityTypeField(SelectOrOtherField):
    select_class = forms.CharField

    def __init__(self, source: str = '', *args, **kwargs):
        self.source = source
        super().__init__(*args, **kwargs)

    def get_bound_field(self, form, field_name):
        # Update radio choices from CDD configuration
        config = get_cdd_config(form.cdd_id)
        values = getattr(config, self.source, {}).get(get_language(), [])
        self.widget.widgets[0].choices = list(zip(values, values)) + [('other', _("Other"))]
        return super().get_bound_field(form, field_name)


class BooleanRadioSelect(forms.RadioSelect):
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        # Override to explicitly set initial selected option to 'False' value
        if value is None:
            context['widget']['optgroups'][0][1][0]['selected'] = True
            context['widget']['optgroups'][0][1][0]['attrs']['checked'] = True
        return context


CustomDatePickerInput = partial(
    DatePickerInput,
    attrs={
        'placeholder': _("dd/mm/yyyy"),
        'autocomplete': 'off',
        **DatePickerInput.defaut_attrs,
    },
)

IsOnlineField = partial(
    forms.BooleanField,
    label=_("Online or in person"),
    initial=False,
    required=False,
    widget=BooleanRadioSelect(choices=((False, _("In person")), (True, _("Online")))),
)


class ActivityFormMixin(forms.BaseForm):
    def __init__(self, parcours_doctoral, *args, **kwargs) -> None:
        self.cdd_id = parcours_doctoral.training.management_entity_id
        super().__init__(*args, **kwargs)

    def clean_start_date(self):
        start_date = self.cleaned_data.get("start_date")
        if start_date and start_date > datetime.date.today():
            raise forms.ValidationError(_("The date cannot be in the future."))
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get("end_date")
        if end_date and end_date > datetime.date.today():
            raise forms.ValidationError(_("The date cannot be in the future."))
        return end_date

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data.get('start_date')
            and cleaned_data.get('end_date')
            and cleaned_data.get('start_date') > cleaned_data.get('end_date')
        ):
            self.add_error('start_date', forms.ValidationError(_("The start date can't be later than the end date")))
        return cleaned_data

    class Media:
        js = [
            # Dates
            'js/moment.min.js',
            'js/locales/moment-fr.js',
            'js/bootstrap-datetimepicker.min.js',
            'js/dates-input.js',
        ]


class ConferenceForm(ActivityFormMixin, forms.ModelForm):
    template_name = "parcours_doctoral/forms/training/conference.html"
    type = ConfigurableActivityTypeField('conference_types', label=_("Activity type"))
    is_online = IsOnlineField()

    class Meta:
        model = Activity
        fields = [
            'type',
            'ects',
            'title',
            'start_date',
            'end_date',
            'participating_days',
            'hour_volume',
            'is_online',
            'website',
            'country',
            'city',
            'organizing_institution',
            'participating_proof',
            'comment',
        ]
        labels = {
            'title': _("Event name"),
            'website': _("Event website"),
            'ects': _("ECTS for the participation"),
        }
        widgets = {
            'start_date': CustomDatePickerInput(),
            'end_date': CustomDatePickerInput(),
            'country': autocomplete.ListSelect2(url="country-autocomplete"),
            'participating_days': forms.NumberInput(attrs={'min': '0', 'step': '0.5'}),
            'ects': forms.NumberInput(attrs={'min': '0', 'step': '0.5'}),
        }
        help_texts = {
            'title': _("Please specify the title in the language of the manifestation"),
            'participating_days': _("Please specify either a hourly volume or a number of participating days"),
            'hour_volume': _("Please specify either a hourly volume or a number of participating days"),
        }

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('participating_days') and not cleaned_data.get('hour_volume'):
            self.add_error(
                'participating_days',
                forms.ValidationError(_("Please specify either a hourly volume or a number of participating days")),
            )
            self.add_error(
                'hour_volume',
                forms.ValidationError(_("Please specify either a hourly volume or a number of participating days")),
            )
        return cleaned_data


class ConferenceCommunicationForm(ActivityFormMixin, forms.ModelForm):
    template_name = "parcours_doctoral/forms/training/conference_communication.html"
    type = SelectOrOtherField(
        label=_("Type of communication"),
        choices=[
            _("Oral presentation"),
            _("Poster"),
        ],
    )

    def clean(self):
        data = super().clean()
        if data.get('committee') != ChoixComiteSelection.YES.name and data.get('acceptation_proof'):
            data['acceptation_proof'] = []
        return data

    class Meta:
        model = Activity
        fields = [
            'type',
            'ects',
            'title',
            'summary',
            'committee',
            'acceptation_proof',
            'dial_reference',
            'participating_proof',
            'comment',
        ]
        labels = {
            'title': _("Title of the communication"),
            'summary': _("Summary of the communication"),
            'acceptation_proof': _("Proof of acceptation by the committee"),
            'participating_proof': _("Attestation of the communication"),
            'committee': _("Selection committee"),
        }
        widgets = {
            'ects': forms.NumberInput(attrs={'min': '0', 'step': '0.5'}),
        }
        help_texts = {
            'title': _("Specify the title in the language of the activity"),
            'participating_proof': _(
                "A document proving that the communication was done (i.e. communication certificate)"
            ),
        }


class ConferencePublicationForm(ActivityFormMixin, forms.ModelForm):
    template_name = "parcours_doctoral/forms/training/conference_publication.html"
    type = ConfigurableActivityTypeField('conference_publication_types', label=_("Publication type"))

    start_date_month = forms.TypedChoiceField(
        choices=month_choices,
        label=_('Month'),
        widget=autocomplete.Select2(),
        required=False,
        coerce=int,
    )
    start_date_year = forms.TypedChoiceField(
        choices=year_choices,
        label=_('Year'),
        widget=autocomplete.Select2(),
        required=False,
        coerce=int,
        help_text=_(
            "For a released text, specify the month and year of publication."
            " Else, specify the month and year of the manuscript."
        ),
    )

    class Meta:
        model = Activity
        fields = [
            'type',
            'ects',
            'title',
            'start_date',
            'publication_status',
            'authors',
            'role',
            'keywords',
            'summary',
            'committee',
            'journal',
            'dial_reference',
            'acceptation_proof',
            'comment',
        ]
        labels = {
            'type': _("Publication type"),
            'title': _("Publication title (in the publication language)"),
            'committee': _("Selection committee"),
            'summary': pgettext_lazy("paper summary", "Summary"),
            'acceptation_proof': _("Proof of acceptance or publication"),
            'publication_status': _("Publication status"),
        }
        widgets = {
            'ects': forms.NumberInput(attrs={'min': '0', 'step': '0.5'}),
        }
        help_texts = {
            'publication_status': _("Refer to the website of your commission for more details."),
            'acceptation_proof': _(
                "Submit a proof, for example a letter from the editor,"
                " a delivery attestation, the first page of the publication, ..."
            ),
            'authors': _(
                'Please use the following format for inputting the first and last name: "Monteiro, M. et Marti, A. C."'
            ),
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')

        if instance and instance.start_date:
            kwargs['initial'] = {
                'start_date_month': instance.start_date.month,
                'start_date_year': instance.start_date.year,
            }

        super().__init__(*args, **kwargs)

    def clean(self):
        data = super().clean()
        if data.get('start_date_year') and data.get('start_date_month'):
            data['start_date'] = datetime.date(data['start_date_year'], data['start_date_month'], 1)
        return data


class CommunicationForm(ActivityFormMixin, forms.ModelForm):
    template_name = "parcours_doctoral/forms/training/communication.html"
    type = ConfigurableActivityTypeField('communication_types', label=_("Activity type"))
    subtype = SelectOrOtherField(
        label=_("Type of communication"),
        choices=[
            _("Oral presentation"),
            _("Poster"),
        ],
    )
    subtitle = forms.CharField(
        label=_("Communication title (in the activity language)"),
        max_length=200,
        required=False,
    )
    is_online = IsOnlineField()

    def clean(self):
        data = super().clean()
        if data.get('committee') != ChoixComiteSelection.YES.name and data.get('acceptation_proof'):
            data['acceptation_proof'] = []
        return data

    class Meta:
        model = Activity
        fields = [
            'type',
            'subtype',
            'title',
            'start_date',
            'is_online',
            'country',
            'city',
            'organizing_institution',
            'website',
            'subtitle',
            'summary',
            'committee',
            'acceptation_proof',
            'participating_proof',
            'dial_reference',
            'ects',
            'comment',
        ]
        labels = {
            'title': _("Event name"),
            'start_date': _("Activity date"),
            'website': _("Event website"),
            'acceptation_proof': _("Proof of acceptation by the committee"),
            'participating_proof': _("Communication attestation"),
            'committee': _("Selection committee"),
            'summary': _("Summary of the communication"),
        }
        widgets = {
            'start_date': CustomDatePickerInput(),
            'country': autocomplete.ListSelect2(url="country-autocomplete"),
            'ects': forms.NumberInput(attrs={'min': '0', 'step': '0.5'}),
        }
        help_texts = {
            'title': _("Specify the name of the event in which the communicate took place"),
            'summary': _(
                "Required field for some of the doctoral commissions. Refer to the website of your commission for "
                "more detail."
            ),
        }


class PublicationForm(ActivityFormMixin, forms.ModelForm):
    template_name = "parcours_doctoral/forms/training/publication.html"
    type = ConfigurableActivityTypeField('publication_types', label=_("Publication type"))

    start_date_month = forms.TypedChoiceField(
        choices=month_choices,
        label=_('Month'),
        widget=autocomplete.Select2(),
        required=False,
        coerce=int,
    )
    start_date_year = forms.TypedChoiceField(
        choices=year_choices,
        label=_('Year'),
        widget=autocomplete.Select2(),
        required=False,
        coerce=int,
        help_text=_("If necessary, specify the date of publication, delivery, acceptation or of the manuscript"),
    )

    class Meta:
        model = Activity
        fields = [
            'type',
            'is_publication_national',
            'title',
            'start_date',
            'authors',
            'role',
            'keywords',
            'summary',
            'journal',
            'publication_status',
            'with_reading_committee',
            'dial_reference',
            'ects',
            'acceptation_proof',
            'comment',
        ]
        labels = {
            'title': _("Title (in the publication language)"),
            'start_date': _("Date"),
            'publication_status': _("Status"),
            'acceptation_proof': _("Attestation"),
        }
        widgets = {
            'ects': forms.NumberInput(attrs={'min': '0', 'step': '0.5'}),
            'is_publication_national': forms.RadioSelect(),
            'with_reading_committee': forms.RadioSelect(),
        }
        help_texts = {
            'publication_status': _(
                "Specify the status of the publication or of the patent. Consult the website of your commission for "
                "more detail."
            ),
            'acceptation_proof': _(
                "Submit a proof, for example a letter from the editor,"
                " a delivery attestation, the first page of the publication, ..."
            ),
            'authors': _(
                'Please use the following format for inputting the first and last name: "Monteiro, M. et Marti, A. C."'
            ),
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        kwargs.setdefault('initial', {})

        if instance is not None and instance.pk is not None:
            if instance.start_date:
                kwargs['initial'].update(
                    {
                        'start_date_month': instance.start_date.month,
                        'start_date_year': instance.start_date.year,
                    }
                )
        else:
            kwargs['initial'].update(
                {
                    'is_publication_national': True,
                    'with_reading_committee': False,
                }
            )

        super().__init__(*args, **kwargs)

    def clean(self):
        data = super().clean()
        if data.get('start_date_year') and data.get('start_date_month'):
            data['start_date'] = datetime.date(data['start_date_year'], data['start_date_month'], 1)
        return data


class ResidencyForm(ActivityFormMixin, forms.ModelForm):
    template_name = "parcours_doctoral/forms/training/residency.html"
    type = ConfigurableActivityTypeField(
        'residency_types',
        label=_("Activity type"),
        help_text=_("Refer to your commission website for more detail."),
    )

    class Meta:
        model = Activity
        fields = [
            'type',
            'ects',
            'subtitle',
            'start_date',
            'end_date',
            'country',
            'city',
            'organizing_institution',
            'participating_proof',
            'comment',
        ]
        labels = {
            'subtitle': _("Activity description"),
            'organizing_institution': _("Institution"),
            'participating_proof': _("Attestation"),
        }
        widgets = {
            'start_date': CustomDatePickerInput(),
            'end_date': CustomDatePickerInput(),
            'country': autocomplete.ListSelect2(url="country-autocomplete"),
            'ects': forms.NumberInput(attrs={'min': '0', 'step': '0.5'}),
        }
        help_texts = {
            'participating_proof': _(
                "Be careful, some doctorales commissions require an activity proof in their"
                " specifics dispositions. Refer to your commission specifics dispositions."
            ),
        }


class ResidencyCommunicationForm(ActivityFormMixin, forms.ModelForm):
    template_name = "parcours_doctoral/forms/training/residency_communication.html"
    type = SelectOrOtherField(choices=[_("Research seminar")], label=_("Activity type"))
    subtype = SelectOrOtherField(
        choices=[_("Oral presentation")],
        label=_("Type of communication"),
        required=False,
    )
    subtitle = forms.CharField(
        label=_("Communication title (in the activity language)"), max_length=200, required=False
    )
    is_online = IsOnlineField()

    class Meta:
        model = Activity
        fields = [
            'type',
            'subtype',
            'title',
            'start_date',
            'is_online',
            'organizing_institution',
            'website',
            'subtitle',
            'ects',
            'summary',
            'participating_proof',
            'comment',
        ]
        labels = {
            'title': _("Event name"),
            'start_date': _("Communication date"),
            'website': _("Event website"),
            'summary': _("Summary of the communication"),
            'participating_proof': _("Attestation of the communication"),
        }
        widgets = {
            'start_date': CustomDatePickerInput(),
            'ects': forms.NumberInput(attrs={'min': '0', 'step': '0.5'}),
        }
        help_texts = {
            'title': _("Specify the name of the event in which the communicate took place"),
            'summary': _(
                "Required field if some doctorals commissions, refer to your commission specifics dispositions."
            ),
        }


class ServiceForm(ActivityFormMixin, forms.ModelForm):
    template_name = "parcours_doctoral/forms/training/service.html"
    type = ConfigurableActivityTypeField(
        "service_types",
        label=_("Service type"),
        help_text=_("Refer to your commission website for more detail."),
    )

    class Meta:
        model = Activity
        fields = [
            'type',
            'title',
            'start_date',
            'end_date',
            'organizing_institution',
            'hour_volume',
            'participating_proof',
            'ects',
            'comment',
        ]
        labels = {
            'title': _("Name or brief description"),
            'start_date': _("Start date"),
            'end_date': _("End date"),
            'subtitle': _("Activity description"),
            'participating_proof': _("Attestation"),
            'organizing_institution': _("Institution"),
        }
        widgets = {
            'start_date': CustomDatePickerInput(),
            'end_date': CustomDatePickerInput(),
            'ects': forms.NumberInput(attrs={'min': '0', 'step': '0.5'}),
        }
        help_texts = {
            'participating_proof': _(
                "Be careful, some doctorales commissions require an activity proof in their"
                " specifics dispositions. Refer to your commission specifics dispositions."
            )
        }


class SeminarForm(ActivityFormMixin, forms.ModelForm):
    template_name = "parcours_doctoral/forms/training/seminar.html"
    type = ConfigurableActivityTypeField("seminar_types", label=_("Activity type"))

    class Meta:
        model = Activity
        fields = [
            'type',
            'title',
            'start_date',
            'end_date',
            'country',
            'city',
            'organizing_institution',
            'hour_volume',
            'hour_volume_type',
            'summary',
            'participating_proof',
            'ects',
        ]
        labels = {
            'title': _("Activity name"),
            'participating_proof': _("Proof of participation for the whole activity"),
        }
        widgets = {
            'start_date': CustomDatePickerInput(),
            'end_date': CustomDatePickerInput(),
            'hour_volume': forms.NumberInput(attrs={'min': '0', 'step': '0.5'}),
            'ects': forms.NumberInput(attrs={'min': '0', 'step': '0.5'}),
        }
        help_texts = {
            'city': _("If the seminar takes place in several places, leave this field empty."),
            'hour_volume': _(
                "Following the specifics of your domain doctoral commission,"
                " specify the total time dedicated to this activity"
            ),
        }


class SeminarCommunicationForm(ActivityFormMixin, forms.ModelForm):
    template_name = "parcours_doctoral/forms/training/seminar_communication.html"
    is_online = IsOnlineField()

    class Meta:
        model = Activity
        fields = [
            'title',
            'start_date',
            'is_online',
            'website',
            'authors',
            'participating_proof',
            'comment',
        ]
        labels = {
            'title': _("Title of the paper in the language of the activity"),
            'start_date': _("Presentation date"),
            'authors': _("First name and last name of the speaker"),
            'participating_proof': _("Certificate of participation in the presentation"),
        }
        widgets = {
            'start_date': CustomDatePickerInput(),
            'country': autocomplete.ListSelect2(url="country-autocomplete"),
            'ects': forms.NumberInput(attrs={'min': '0', 'step': '0.5'}),
        }


class ValorisationForm(ActivityFormMixin, forms.ModelForm):
    template_name = "parcours_doctoral/forms/training/valorisation.html"

    class Meta:
        model = Activity
        fields = [
            'title',
            'subtitle',
            'summary',
            'participating_proof',
            'ects',
            'comment',
        ]
        labels = {
            'title': pgettext_lazy("admission", "Title"),
            'subtitle': _("Description"),
            'summary': _("Detailed curriculum vitae"),
            'participating_proof': _("Proof"),
        }
        widgets = {
            'ects': forms.NumberInput(attrs={'min': '0', 'step': '0.5'}),
        }


class CourseForm(ActivityFormMixin, forms.ModelForm):
    template_name = "parcours_doctoral/forms/training/course.html"
    type = ConfigurableActivityTypeField("course_types", label=pgettext_lazy("parcours_doctoral course", "Course type"))
    subtitle = forms.CharField(
        label=_("Course unit code (if applicable)"),
        help_text=_("As it appears in an official course catalogue"),
        max_length=200,
        required=False,
    )
    organizing_institution = SelectOrOtherField(choices=[INSTITUTION_UCL], label=_("Institution"))
    academic_year = AcademicYearModelChoiceField(widget=autocomplete.ListSelect2(), required=False)
    is_online = forms.BooleanField(
        label=_("Course unit with evaluation"),  # Yes, its another meaning, but we spare a db field
        initial=False,
        required=False,
        widget=BooleanRadioSelect(choices=((False, _("No")), (True, _("Yes")))),
    )

    def __init__(self, parcours_doctoral, *args, **kwargs) -> None:
        super().__init__(parcours_doctoral, *args, **kwargs)
        # Convert from dates to year if UCLouvain
        if (
            self.instance
            and self.instance.organizing_institution == INSTITUTION_UCL
            and self.instance.start_date
            and self.instance.end_date
        ):
            self.fields['academic_year'].initial = AcademicYear.objects.get(
                start_date=self.instance.start_date,
                end_date=self.instance.end_date,
            )

    def clean(self):
        cleaned_data = super().clean()
        # Convert from academic year to dates if UCLouvain
        if cleaned_data.get('organizing_institution') == INSTITUTION_UCL and cleaned_data.get('academic_year'):
            cleaned_data['start_date'] = cleaned_data['academic_year'].start_date
            cleaned_data['end_date'] = cleaned_data['academic_year'].end_date
        cleaned_data.pop('academic_year', None)
        return cleaned_data

    class Meta:
        model = Activity
        fields = [
            'type',
            'title',
            'subtitle',
            'organizing_institution',
            'start_date',
            'end_date',
            'hour_volume',
            'authors',
            'is_online',
            'mark',
            'ects',
            'participating_proof',
            'comment',
        ]
        widgets = {
            'start_date': CustomDatePickerInput(),
            'end_date': CustomDatePickerInput(),
            'ects': forms.NumberInput(attrs={'min': '0', 'step': '0.5'}),
        }
        labels = {
            'title': pgettext_lazy("parcours_doctoral course", "Title"),
            'authors': _("Organisers or academic responsibles"),
            'hour_volume': _("Hourly volume"),
            'participating_proof': _("Proof of participation or success"),
        }
        help_texts = {
            'authors': _("In the context of a course, specify the name of the professor"),
            'title': _("As it appears in an official course catalogue"),
        }


class ComplementaryCourseForm(CourseForm):
    """Course form for complementary training"""

    type = ConfigurableActivityTypeField("complementary_course_types", label=_("Activity type"))

    def __init__(self, parcours_doctoral, *args, **kwargs):
        super().__init__(parcours_doctoral, *args, **kwargs)
        self.instance.context = ContexteFormation.COMPLEMENTARY_TRAINING.name


class PaperForm(ActivityFormMixin, forms.ModelForm):
    template_name = "parcours_doctoral/forms/training/paper.html"
    type = forms.ChoiceField(label=_("Type of paper"), choices=ChoixTypeEpreuve.choices())

    class Meta:
        model = Activity
        fields = [
            'type',
            'ects',
            'comment',
        ]
        widgets = {
            'ects': forms.NumberInput(attrs={'min': '0', 'step': '0.5'}),
        }

    def __init__(self, parcours_doctoral: ParcoursDoctoral, *args, **kwargs):
        super().__init__(parcours_doctoral, *args, **kwargs)

        # Only one paper of each type can be created
        paper_qs = parcours_doctoral.activity_set.filter(category=CategorieActivite.PAPER.name)

        if self.instance.pk is not None:
            paper_qs = paper_qs.exclude(type=self.instance.type)
        elif self.data.get('type'):
            paper_qs = paper_qs.exclude(type=self.data.get('type'))

        unavailable_papers_types = paper_qs.values_list('type', flat=True)

        self.fields['type'].choices = (
            (enum.name, enum.value) for enum in ChoixTypeEpreuve if enum.name not in unavailable_papers_types
        )


class UclCourseForm(ActivityFormMixin, forms.ModelForm):
    template_name = "parcours_doctoral/forms/training/ucl_course.html"
    academic_year = AcademicYearModelChoiceField(
        to_field_name='year',
        widget=autocomplete.ListSelect2(),
    )
    learning_unit_year = forms.CharField(
        label=pgettext_lazy("admission", "Learning unit"),
        widget=autocomplete.ListSelect2(
            url='admission:autocomplete:learning-unit-years-and-classes',
            attrs={
                'data-html': True,
                'data-placeholder': _('Search for an EU code'),
                'data-minimum-input-length': 3,
            },
            forward=[Field("academic_year", "annee")],
        ),
    )

    def __init__(self, parcours_doctoral: ParcoursDoctoral, *args, **kwargs):
        super().__init__(parcours_doctoral, *args, **kwargs)
        self.fields['learning_unit_year'].required = True
        # Filter out disabled contexts
        choices = dict(self.fields['context'].widget.choices)
        if not parcours_doctoral.training.management_entity.doctorate_config.is_complementary_training_enabled:
            del choices[ContexteFormation.COMPLEMENTARY_TRAINING.name]
        self.fields['context'].widget.choices = list(choices.items())

        # Initialize values
        if self.initial.get('learning_unit_year'):
            learning_unit_year = LearningUnitYear.objects.get(pk=self.initial['learning_unit_year'])
            self.initial['academic_year'] = learning_unit_year.academic_year.year
            self.initial['learning_unit_year'] = learning_unit_year.acronym
            self.fields['learning_unit_year'].widget.choices = [
                (
                    learning_unit_year.acronym,
                    f"{learning_unit_year.acronym} - {learning_unit_year.complete_title_i18n}",
                ),
            ]

        current_year = current_academic_year().year
        selectable_years = [current_year, current_year + 1]

        if self.initial.get('academic_year'):
            selectable_years.append(self.initial['academic_year'])

        self.fields['academic_year'].queryset = self.fields['academic_year'].queryset.filter(year__in=selectable_years)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('academic_year') and cleaned_data.get('learning_unit_year'):
            cleaned_data['learning_unit_year'] = LearningUnitYear.objects.get(
                academic_year=cleaned_data['academic_year'],
                acronym=cleaned_data['learning_unit_year'],
            )
        else:
            if not cleaned_data.get('academic_year'):
                self.add_error('academic_year', forms.ValidationError(_("Please choose a correct academic year.")))
            if not cleaned_data.get('learning_unit_year'):
                self.add_error('learning_unit_year', forms.ValidationError(_("Please choose a correct learning unit.")))
            else:
                # Remove the value as it is not a LearningUnitYear instance and it would cause an error later.
                del cleaned_data['learning_unit_year']
        return cleaned_data

    class Meta:
        model = Activity
        fields = [
            'context',
            'academic_year',
            'learning_unit_year',
        ]


class UclCompletedCourseForm(ActivityFormMixin, forms.ModelForm):
    template_name = "parcours_doctoral/forms/training/ucl_completed_course.html"

    corrected_mark = forms.CharField(
        label=_('Corrected mark'),
        required=False,
        max_length=200,
    )

    assessment_to_correct_uuid = forms.UUIDField(
        required=False,
        widget=forms.HiddenInput,
    )

    class Meta(CourseForm.Meta):
        model = Activity
        fields = [
            'hour_volume',
            'authors',
            'ects',
            'participating_proof',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize the corrected mark of the last assessment, if any
        self.final_assessment: Optional[AssessmentEnrollment] = None
        self.assessments = []

        if self.instance:
            self.assessments = self.instance.assessmentenrollment_set.with_session_numero().order_by('-session_numero')
            self.final_assessment = self.assessments.first()

            if self.final_assessment:
                self.fields['corrected_mark'].initial = self.final_assessment.corrected_mark
                self.fields['assessment_to_correct_uuid'].initial = self.final_assessment.uuid

    def clean_assessment_to_correct_uuid(self):
        assessment_to_correct_uuid = self.cleaned_data.get('assessment_to_correct_uuid')

        # Check that the submitted mark is specified for the right assessment
        if self.final_assessment and self.final_assessment.uuid != assessment_to_correct_uuid:
            initial_session = next(
                (
                    Session.get_value(assessment.session)
                    for assessment in self.assessments
                    if assessment.uuid == assessment_to_correct_uuid
                ),
                _('Not determined'),
            )

            self.add_error(
                'corrected_mark',
                _(
                    'Please be sure the corrected mark is related to the desired session '
                    '(initially: "%(initial_session)s", now: "%(target_session)s").'
                )
                % {
                    'initial_session': initial_session,
                    'target_session': Session.get_value(self.final_assessment.session),
                },
            )

        return assessment_to_correct_uuid

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)

        # Save the final assessment corrected mark if any
        if self.final_assessment:
            self.final_assessment.corrected_mark = self.cleaned_data['corrected_mark']
            self.final_assessment.save(update_fields=['corrected_mark'])

        return instance
