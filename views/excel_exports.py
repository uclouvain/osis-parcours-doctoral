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

import ast
from typing import Dict

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.template.defaultfilters import yesno
from django.urls import reverse
from django.utils.html import format_html
from django.utils.text import slugify
from django.utils.translation import gettext as _, pgettext
from django.utils.translation import gettext_lazy
from django.views import View
from osis_async.models import AsyncTask
from osis_export.contrib.export_mixins import ExcelFileExportMixin, ExportMixin
from osis_export.models import Export
from osis_export.models.enums.types import ExportTypes

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixTypeAdmission,
)
from admission.utils import add_messages_into_htmx_response
from base.models.person import Person
from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.domain.model.enums import (
    ChoixStatutParcoursDoctoral,
    ChoixTypeFinancement,
)
from parcours_doctoral.ddd.read_view.dto.parcours_doctoral import (
    ParcoursDoctoralRechercheDTO,
)
from parcours_doctoral.ddd.read_view.queries import ListerTousParcoursDoctorauxQuery
from parcours_doctoral.forms.list import ParcoursDoctorauxFilterForm

__all__ = [
    'ParcoursDoctoralListExcelExportView',
]


FULL_DATE_FORMAT = '%Y/%m/%d, %H:%M:%S'
SHORT_DATE_FORMAT = '%Y/%m/%d'


class ParcoursDoctoralListExcelExportView(
    PermissionRequiredMixin,
    ExportMixin,
    ExcelFileExportMixin,
    View,
):
    permission_required = 'parcours_doctoral.view_parcours_doctoral'
    description = gettext_lazy('Doctoral trainings')
    redirect_url_name = 'parcours_doctoral:list'
    export_name = gettext_lazy('Doctoral trainings export')
    export_description = gettext_lazy('Excel export of doctoral trainings')
    success_message = gettext_lazy(
        'Your export request has been planned, you will receive a notification as soon as it is available.'
    )
    failure_message = gettext_lazy('The export has failed')

    with_parameters_worksheet = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.language = settings.LANGUAGE_CODE

    def generate_file(self, person, filters, **kwargs):
        # Get the person language
        if person.language:
            self.language = person.language
        return super().generate_file(person, filters, **kwargs)

    def get_export_objects(self, **kwargs):
        # The filters are saved as dict string so we convert it here to a dict
        filters = ast.literal_eval(kwargs.get('filters'))
        return message_bus_instance.invoke(ListerTousParcoursDoctorauxQuery(**filters))

    def get(self, request):
        # Get filters
        filters = self.get_filters()
        export = None

        if filters:
            # Create async task
            task = AsyncTask.objects.create(
                name=self.export_name,
                description=self.export_description,
                person=self.request.user.person,
            )

            # Create export
            export = Export.objects.create(
                called_from_class=f'{self.__module__}.{self.__class__.__name__}',
                filters=self.get_filters(),
                person=self.request.user.person,
                job_uuid=task.uuid,
                file_name=slugify(self.export_name),
                type=ExportTypes.EXCEL.name,
                extra_data={'description': str(self.export_description)},
            )

        if export:
            messages.success(request, self.success_message)
        else:
            messages.error(request, self.failure_message)

        if self.request.htmx:
            response = HttpResponse(self.success_message if export else self.failure_message)
            add_messages_into_htmx_response(
                request=request,
                response=response,
            )
            return response

        return HttpResponseRedirect(reverse(self.redirect_url_name))

    def get_filters(self):
        form = ParcoursDoctorauxFilterForm(user=self.request.user, data=self.request.GET)
        if form.is_valid():
            filters = form.cleaned_data
            filters.pop('taille_page', None)
            filters.pop('page', None)
            filters.pop('instituts_secteurs', None)

            ordering_field = self.request.GET.get('o')
            if ordering_field:
                filters['tri_inverse'] = ordering_field[0] == '-'
                filters['champ_tri'] = ordering_field.lstrip('-')

            filters['demandeur'] = str(self.request.user.person.uuid)
            return form.cleaned_data
        return {}

    def get_task_done_async_manager_extra_kwargs(self, file_name: str, file_url: str, export_extra_data: Dict) -> Dict:
        download_message = format_html(
            "{}: <a href='{}' target='_blank'>{}</a>",
            _("Your document is available here"),
            file_url,
            file_name,
        )
        description = export_extra_data.get('description')
        return {'description': f"{description}<br>{download_message}"}

    def get_read_token_extra_kwargs(self) -> Dict:
        return {'custom_ttl': settings.EXPORT_FILE_DEFAULT_TTL}

    def get_formatted_filters_parameters_worksheet(self, filters: str) -> Dict:
        formatted_filters = super().get_formatted_filters_parameters_worksheet(filters)

        formatted_filters.pop('demandeur', None)
        formatted_filters.pop('tri_inverse', None)
        formatted_filters.pop('champ_tri', None)

        # Formatting of the names of the filters
        base_fields = ParcoursDoctorauxFilterForm.base_fields
        mapping_filter_key_name = {
            key: str(base_fields[key].label) if key in base_fields else key for key in formatted_filters
        }

        # Formatting of the values of the filters
        mapping_filter_key_value = {}

        # Retrieve candidate name
        student_global_id = formatted_filters.get('matricule_doctorant')
        if student_global_id:
            person = Person.objects.filter(global_id=student_global_id).first()
            if person:
                mapping_filter_key_value['matricule_doctorant'] = person.full_name

        # Format enums
        statuses = formatted_filters.get('statuts')
        if statuses:
            mapping_filter_key_value['statuts'] = [
                ChoixStatutParcoursDoctoral[status_key].value for status_key in statuses
            ]

        values = formatted_filters.get('type_admission')
        if values:
            mapping_filter_key_value['type_admission'] = [ChoixTypeAdmission[key].value for key in values]

        values = formatted_filters.get('type_financement')
        if values:
            mapping_filter_key_value['type_financement'] = [ChoixTypeFinancement[key].value for key in values]

        # Format boolean values
        mapping_filter_key_value['fnrs_fria_fresh'] = yesno(formatted_filters.get('fnrs_fria_fresh'), _('Yes,No,All'))

        return {
            mapping_filter_key_name[key]: mapping_filter_key_value.get(key, formatted_filters[key])
            for key, value in formatted_filters.items()
        }

    def get_header(self):
        return [
            _('Dossier numero'),
            _('Student'),
            _('Scholarship holder'),
            _('Course'),
            _('Status'),
            _('Admission date'),
            _('Pre-admission'),
            _('Cotutelle'),
            pgettext('parcours_doctoral', 'Additional training'),
            _('In order of registration'),
            _('Validated credits total'),
        ]

    def get_row_data(self, row: ParcoursDoctoralRechercheDTO):
        return [
            row.reference,
            f'{row.nom_doctorant}, {row.prenom_doctorant}',
            row.code_bourse,
            row.formation.nom_complet,
            row.statut,
            row.cree_le.strftime(SHORT_DATE_FORMAT) if row.cree_le else "",
            yesno(row.type_admission == ChoixTypeAdmission.PRE_ADMISSION.name),
            yesno(row.cotutelle),
            yesno(row.formation_complementaire),
            "",
            row.total_credits_valides,
        ]
