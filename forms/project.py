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
from dal import forward
from django import forms
from django.utils.translation import gettext_lazy as _
from osis_document_components.fields import FileUploadField

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixDoctoratDejaRealise,
    ChoixTypeAdmission,
)
from admission.utils import (
    get_language_initial_choices,
    get_thesis_location_initial_choices,
)
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.forms.utils.autocomplete import ListSelect2
from base.forms.utils.datefield import CustomDateInput
from base.forms.utils.fields import RadioBooleanField
from base.models.entity_version import EntityVersion
from base.models.enums.entity_type import EntityType
from base.models.enums.organization_type import MAIN

LANGUAGE_UNDECIDED = 'XX'


class ProjectForm(forms.Form):
    lieu_these = forms.CharField(
        label=_('Thesis location'),
        required=False,
        help_text=_(
            'If known, indicate, for example, the name of the laboratory, clinical department, research centre, '
            '... where the thesis will be carried out at UCLouvain'
        ),
        max_length=255,
    )
    titre = forms.CharField(
        label=_('Project title'),
        required=False,
        max_length=1023,
    )
    resume = forms.CharField(
        label=_('Project abstract (max. 4000 characters)'),
        help_text=_('Write your abstract in the language decided with your accompanying committee.'),
        required=False,
        widget=forms.Textarea,
    )
    documents_projet = FileUploadField(
        label=_('Doctoral research project'),
        required=False,
    )
    graphe_gantt = FileUploadField(
        label=_('Gantt chart'),
        required=False,
    )
    proposition_programme_doctoral = FileUploadField(
        label=_('Doctoral training proposal'),
        required=False,
    )
    projet_formation_complementaire = FileUploadField(
        label=_('Complementary training proposition'),
        required=False,
        help_text=_(
            'Depending on your previous experience and your research project, the PhD Committee may require you to '
            'take additional PhD training, up to a maximum of 60 credits. If so, please indicate here a proposal '
            'for additional training.'
        ),
    )
    lettres_recommandation = FileUploadField(
        label=_('Letters of recommendation'),
        required=False,
    )
    langue_redaction_these = forms.CharField(
        label=_('Thesis language'),
        widget=ListSelect2(
            url='language-autocomplete',
        ),
        required=False,
    )
    institut_these = forms.CharField(
        label=_('Research institute'),
        required=False,
        widget=ListSelect2(
            url='admission:autocomplete:entities',
            forward=[
                forward.Const(MAIN, 'organization_type'),
                forward.Const(EntityType.INSTITUTE.name, 'entity_type'),
            ],
        ),
    )

    projet_doctoral_deja_commence = RadioBooleanField(
        label=_('Has your PhD project already started?'),
        required=False,
        initial=False,
    )
    projet_doctoral_institution = forms.CharField(
        label=_('Institution'),
        required=False,
        max_length=255,
    )
    projet_doctoral_date_debut = forms.DateField(
        label=_('Research start date'),
        widget=CustomDateInput(),
        required=False,
    )
    doctorat_deja_realise = forms.ChoiceField(
        label=_('Have you previously enrolled for a PhD?'),
        choices=ChoixDoctoratDejaRealise.choices(),
        initial=ChoixDoctoratDejaRealise.NO.name,
        required=False,
        help_text=_('Indicate any completed or interrupted PhD studies in which you are no longer enrolled.'),
    )
    institution = forms.CharField(
        label=_('Institution in which the PhD thesis has been realised / started'),
        required=False,
        max_length=255,
    )
    domaine_these = forms.CharField(
        label=_('Doctorate thesis field'),
        required=False,
        max_length=255,
    )
    non_soutenue = forms.BooleanField(
        label=_('No defence'),
        required=False,
    )
    date_soutenance = forms.DateField(
        label=_('Defence date'),
        widget=CustomDateInput(),
        required=False,
    )
    raison_non_soutenue = forms.CharField(
        label=_('No defence reason'),
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        max_length=255,
    )

    class Media:
        js = ('js/dependsOn.min.js',)

    def __init__(self, admission_type, *args, **kwargs):
        self.is_admission = admission_type == ChoixTypeAdmission.ADMISSION.name

        super().__init__(*args, **kwargs)

        self.label_classes = self.get_field_label_classes()

        # Add the specified thesis position in the choices of the related field
        self.fields['lieu_these'].widget.choices = get_thesis_location_initial_choices(
            self.data.get(self.add_prefix('lieu_these'), self.initial.get('lieu_these')),
        )
        if self.data.get(self.add_prefix('raison_non_soutenue'), self.initial.get('raison_non_soutenue')):
            self.fields['non_soutenue'].initial = True

        thesis_institute = self.data.get(self.add_prefix('institut_these'), self.initial.get('institut_these'))
        if thesis_institute:
            institute_obj = EntityVersion.objects.filter(uuid=thesis_institute).only('uuid', 'acronym', 'title').first()

            if institute_obj:
                self.fields['institut_these'].widget.choices = [
                    (
                        institute_obj.uuid,
                        '{title} ({acronym})'.format(title=institute_obj.title, acronym=institute_obj.acronym),
                    ),
                ]

        lang_code = self.data.get(self.add_prefix('langue_redaction_these'), self.initial.get('langue_redaction_these'))
        self.fields['langue_redaction_these'].widget.choices = (
            ((LANGUAGE_UNDECIDED, _('Undecided')),)
            if lang_code == LANGUAGE_UNDECIDED
            else get_language_initial_choices(lang_code)
        )

        # Initialize some fields if they are not already set in the input data
        for field in [
            'projet_doctoral_deja_commence',
            'doctorat_deja_realise',
        ]:
            if self.initial.get(field) in {None, ''}:
                self.initial[field] = self.fields[field].initial

    def clean(self):
        cleaned_data = super().clean()

        # Some consistency checks and cleaning
        if cleaned_data['doctorat_deja_realise'] not in [
            ChoixDoctoratDejaRealise.YES.name,
        ]:
            cleaned_data['institution'] = ''
            cleaned_data['domaine_these'] = ''
            cleaned_data['non_soutenue'] = None
            cleaned_data['date_soutenance'] = None
            cleaned_data['raison_non_soutenue'] = ''

        else:
            if not cleaned_data.get('domaine_these'):
                self.add_error('domaine_these', FIELD_REQUIRED_MESSAGE)

            if not cleaned_data.get('institution'):
                self.add_error('institution', FIELD_REQUIRED_MESSAGE)

            if cleaned_data.get('non_soutenue'):
                cleaned_data['date_soutenance'] = None

                if not cleaned_data.get('raison_non_soutenue'):
                    self.add_error('raison_non_soutenue', FIELD_REQUIRED_MESSAGE)

            else:
                cleaned_data['raison_non_soutenue'] = ''

        return cleaned_data

    def get_field_label_classes(self):
        """Returns the classes that should be applied to the label of the form fields."""

        possible_mandatory_fields = [
            'raison_non_soutenue',
            'titre',
        ]

        if self.is_admission:
            possible_mandatory_fields += [
                'resume',
                'documents_projet',
                'proposition_programme_doctoral',
                'langue_redaction_these',
                'projet_doctoral_deja_commence',
                'projet_doctoral_institution',
                'projet_doctoral_date_debut',
                'institution',
                'domaine_these',
            ]

        return {field_name: 'required_text' for field_name in possible_mandatory_fields}
