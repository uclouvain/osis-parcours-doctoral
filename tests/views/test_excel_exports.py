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
import datetime
from decimal import Decimal
from typing import List

import freezegun
from django.contrib.auth.models import User
from django.template.defaultfilters import yesno
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.translation import gettext as _
from osis_async.models import AsyncTask
from osis_async.models.enums import TaskState
from osis_export.models import Export
from osis_export.models.enums.types import ExportTypes

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixTypeAdmission,
)
from base.models.enums.entity_type import EntityType
from base.tests import QueriesAssertionsMixin
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.read_view.dto.formation import FormationRechercheDTO
from parcours_doctoral.ddd.read_view.dto.parcours_doctoral import (
    ParcoursDoctoralRechercheDTO,
)
from parcours_doctoral.ddd.read_view.queries import ListerTousParcoursDoctorauxQuery
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.roles import AdreSecretaryRoleFactory
from parcours_doctoral.views.excel_exports import (
    SHORT_DATE_FORMAT,
    ParcoursDoctoralListExcelExportView,
)
from reference.tests.factories.country import CountryFactory


class UnfrozenDTO:
    # Trick to make this "unfrozen" just for tests
    def __setattr__(self, key, value):
        object.__setattr__(self, key, value)

    def __delattr__(self, item):
        object.__delattr__(self, item)


class _ParcoursDoctoralRechercheDTO(UnfrozenDTO, ParcoursDoctoralRechercheDTO):
    pass


@freezegun.freeze_time('2023-01-01')
class ParcoursDoctoralListExcelExportViewTestCase(QueriesAssertionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        # Users
        cls.user = User.objects.create_user(
            username='john_doe',
            password='top_secret',
        )

        cls.adre_user = AdreSecretaryRoleFactory().person.user

        # Academic years
        AcademicYearFactory.produce(base_year=2023, number_past=2, number_future=2)

        # Entities
        faculty_entity = EntityFactory()
        EntityVersionFactory(
            entity=faculty_entity,
            acronym='ABCDEF',
            entity_type=EntityType.FACULTY.name,
        )

        cls.first_entity = EntityFactory()
        EntityVersionFactory(
            entity=cls.first_entity,
            acronym='GHIJK',
            entity_type=EntityType.SCHOOL.name,
            parent=faculty_entity,
        )

        # Admissions
        cls.parcours_doctoral = ParcoursDoctoralFactory(
            student__country_of_citizenship=CountryFactory(european_union=True, name='Belgique'),
            student__first_name="John",
            student__last_name="Doe",
            student__private_email="jdoe@example.be",
            status=ChoixStatutParcoursDoctoral.ADMIS.name,
            training__management_entity=cls.first_entity,
            training__acronym="ABCD0",
            other_international_scholarship='scholarship',
        )

        cls.lite_reference = '{:07,}'.format(cls.parcours_doctoral.reference).replace(',', '.')

        cls.result = _ParcoursDoctoralRechercheDTO(
            uuid=cls.parcours_doctoral.uuid,
            reference=f'M-ABCDEF22-{cls.lite_reference}',
            statut=cls.parcours_doctoral.status,
            type_admission=cls.parcours_doctoral.admission.type,
            formation=FormationRechercheDTO(
                sigle=cls.parcours_doctoral.training.acronym,
                code=cls.parcours_doctoral.training.partial_acronym,
                annee=cls.parcours_doctoral.training.academic_year.year,
                intitule=cls.parcours_doctoral.training.title,
                intitule_fr=cls.parcours_doctoral.training.title,
                intitule_en=cls.parcours_doctoral.training.title_english,
                type=cls.parcours_doctoral.training.education_group_type.name,
            ),
            matricule_doctorant=cls.parcours_doctoral.student.global_id,
            genre_doctorant=cls.parcours_doctoral.student.gender,
            prenom_doctorant=cls.parcours_doctoral.student.first_name,
            nom_doctorant=cls.parcours_doctoral.student.last_name,
            code_bourse=cls.parcours_doctoral.other_international_scholarship,
            cotutelle=cls.parcours_doctoral.cotutelle,
            formation_complementaire=False,
            en_regle_inscription=False,
            total_credits_valides=0,
            cree_le=cls.parcours_doctoral.created_at,
            date_admission_par_cdd=datetime.datetime(2020, 1, 1),
        )
        cls.default_params = {
            'annee_academique': 2022,
            'taille_page': 10,
            'demandeur': str(cls.adre_user.person.uuid),
        }

        # Targeted url
        cls.url = reverse('parcours_doctoral:excel-exports')
        cls.list_url = reverse('parcours_doctoral:list')

    def test_export_user_without_person(self):
        self.client.force_login(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_export_adre_user(self):
        self.client.force_login(user=self.adre_user)

        response = self.client.get(self.url)
        self.assertRedirects(response, expected_url=self.list_url, fetch_redirect_response=False)

        response = self.client.get(
            self.url,
            **{"HTTP_HX-Request": 'true'},
        )

        self.assertEqual(response.status_code, 200)

    def test_export_with_adre_user_without_filters_doesnt_plan_the_export(self):
        self.client.force_login(user=self.adre_user)

        response = self.client.get(self.url)

        self.assertRedirects(response, expected_url=self.list_url, fetch_redirect_response=False)

        task = AsyncTask.objects.filter(person=self.adre_user.person).first()
        self.assertIsNone(task)

        export = Export.objects.filter(person=self.adre_user.person).first()
        self.assertIsNone(export)

    def test_export_with_adre_user_with_filters_plans_the_export(self):
        self.client.force_login(user=self.adre_user)

        response = self.client.get(self.url, data=self.default_params)

        self.assertRedirects(response, expected_url=self.list_url, fetch_redirect_response=False)

        task = AsyncTask.objects.filter(person=self.adre_user.person).first()
        self.assertIsNotNone(task)
        self.assertEqual(task.name, _('Doctoral trainings export'))
        self.assertEqual(task.description, _('Excel export of doctoral trainings'))
        self.assertEqual(task.state, TaskState.PENDING.name)

        export = Export.objects.filter(job_uuid=task.uuid).first()
        self.assertIsNotNone(export)
        self.assertEqual(
            export.called_from_class, 'parcours_doctoral.views.excel_exports.ParcoursDoctoralListExcelExportView'
        )
        self.assertEqual(export.file_name, 'export-des-parcours-doctoraux')
        self.assertEqual(export.type, ExportTypes.EXCEL.name)

        filters = ast.literal_eval(export.filters)
        self.assertEqual(filters.get('annee_academique'), self.default_params.get('annee_academique'))
        self.assertEqual(filters.get('demandeur'), self.default_params.get('demandeur'))

    def test_export_with_adre_user_with_filters_and_asc_ordering(self):
        self.client.force_login(user=self.adre_user)

        # With asc ordering
        response = self.client.get(self.url, data={**self.default_params, 'o': 'numero_demande'})

        self.assertRedirects(response, expected_url=self.list_url, fetch_redirect_response=False)

        task = AsyncTask.objects.filter(person=self.adre_user.person).first()
        self.assertIsNotNone(task)

        export = Export.objects.filter(job_uuid=task.uuid).first()
        self.assertIsNotNone(export)

        filters = ast.literal_eval(export.filters)
        self.assertEqual(filters.get('annee_academique'), self.default_params.get('annee_academique'))
        self.assertEqual(filters.get('demandeur'), self.default_params.get('demandeur'))
        self.assertEqual(filters.get('tri_inverse'), False)
        self.assertEqual(filters.get('champ_tri'), 'numero_demande')

    def test_export_with_adre_user_with_filters_and_desc_ordering(self):
        self.client.force_login(user=self.adre_user)

        # With asc ordering
        response = self.client.get(self.url, data={**self.default_params, 'o': '-numero_demande'})

        self.assertRedirects(response, expected_url=self.list_url, fetch_redirect_response=False)

        task = AsyncTask.objects.filter(person=self.adre_user.person).first()
        self.assertIsNotNone(task)

        export = Export.objects.filter(job_uuid=task.uuid).first()
        self.assertIsNotNone(export)

        filters = ast.literal_eval(export.filters)
        self.assertEqual(filters.get('annee_academique'), self.default_params.get('annee_academique'))
        self.assertEqual(filters.get('demandeur'), self.default_params.get('demandeur'))
        self.assertEqual(filters.get('tri_inverse'), True)
        self.assertEqual(filters.get('champ_tri'), 'numero_demande')

    def test_export_content(self):
        view = ParcoursDoctoralListExcelExportView()
        header = view.get_header()

        ParcoursDoctoralFactory()

        results: List[ParcoursDoctoralRechercheDTO] = message_bus_instance.invoke(
            ListerTousParcoursDoctorauxQuery(numero=self.parcours_doctoral.reference)
        )

        self.assertEqual(len(results), 1)

        result = results[0]

        row_data = view.get_row_data(result)

        self.assertEqual(len(header), len(row_data))

        self.assertEqual(row_data[0], result.reference)
        self.assertEqual(row_data[1], f'{result.nom_doctorant}, {result.prenom_doctorant}')
        self.assertEqual(row_data[2], result.code_bourse)
        self.assertEqual(row_data[3], result.formation.nom_complet)
        self.assertEqual(row_data[4], result.statut)
        self.assertEqual(row_data[5], result.cree_le.strftime(SHORT_DATE_FORMAT))
        self.assertEqual(row_data[6], yesno(result.type_admission == ChoixTypeAdmission.PRE_ADMISSION.name))
        self.assertEqual(row_data[7], yesno(result.cotutelle))
        self.assertEqual(row_data[8], yesno(result.formation_complementaire))
        self.assertEqual(row_data[9], '')
        self.assertEqual(row_data[10], Decimal('0'))
