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
import datetime
from copy import deepcopy
from decimal import Decimal
from functools import partial
from io import BytesIO
from unittest import mock
from unittest.mock import MagicMock, Mock

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import QuerySet
from django.shortcuts import resolve_url
from django.test import TestCase
from django.utils.translation import gettext_lazy
from osis_signature.enums import SignatureState

from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixTypeAdmission
from admission.tests.factories.doctorate import DoctorateFactory
from admission.tests.factories.person import CompletePersonFactory, InternalPersonFactory
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.models.entity import Entity
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import ExternalPersonFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.student import StudentFactory
from base.tests.factories.tutor import TutorFactory
from epc.tests.factories.inscription_programme_annuel import InscriptionProgrammeAnnuelFactory
from parcours_doctoral.auth.roles.ca_member import CommitteeMember
from parcours_doctoral.auth.roles.promoter import Promoter
from parcours_doctoral.ddd.domain.model.enums import ChoixSousDomaineSciences, ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ENTITY_CDE
from parcours_doctoral.ddd.formation.domain.model.enums import CategorieActivite, ContexteFormation
from parcours_doctoral.models import (
    Activity,
    ActorType,
    ConfirmationPaper,
    ParcoursDoctoral,
    ParcoursDoctoralSupervisionActor,
)
from parcours_doctoral.views.config.doctorate_import_from_xlsx import ChoixOuiNon
from reference.tests.factories.country import CountryFactory


class DoctorateImportFromXLSXViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.url = resolve_url('parcours_doctoral:config:doctorate-import-from-xlsx')

        cls.academic_years = [AcademicYearFactory(year=year) for year in [2020, 2021, 2022]]

        cls.commission: Entity = EntityFactory()
        cls.commission_version = EntityVersionFactory(entity=cls.commission, acronym=ENTITY_CDE)

        cls.training = DoctorateFactory(
            management_entity=cls.commission,
            academic_year=cls.academic_years[0],
            education_group_type__name=TrainingType.PHD.name,
        )

        cls.country = CountryFactory(iso_code='FR')

        cls.candidate = CompletePersonFactory(language=settings.LANGUAGE_CODE_FR)

        cls.student = StudentFactory(person=cls.candidate, registration_id='01234567')

        cls.internal_student_not_tutor = StudentFactory(person=InternalPersonFactory()).person
        cls.internal_student_and_tutor = TutorFactory(
            person=StudentFactory(person=InternalPersonFactory()).person
        ).person

        cls.internal_person = InternalPersonFactory()
        cls.external_person = ExternalPersonFactory()

        cls.fac_manager_user = ProgramManagerFactory(education_group=cls.training.education_group).person.user

    def mock_iter_rows(self, current_list, **kwargs):
        if kwargs.get('values_only'):
            for row in current_list:
                yield [cell.value for cell in row]
            return
        for row in current_list:
            yield [cell for cell in row]
        return

    def get_example_file(self):
        loaded_file = BytesIO(b'data1;data2;data3')
        loaded_file.name = 'my_file.xlsx'
        return SimpleUploadedFile(loaded_file.name, loaded_file.getvalue())

    def mock_cell(self, current_list: list[tuple], row, column, value):
        cell = current_list[row - 1][column - 1]
        cell.value = value
        return cell

    def setUp(self):
        super().setUp()

        self.doctorate_first_row_cells = {
            'identification_noma': Mock(value=''),
            'identification_nom_etudiant': Mock(value=''),
            'choix_formation_admission_preadmission': Mock(value=''),
            'choix_formation_secteur': Mock(value=''),
            'choix_formation_sigle_doctorat': Mock(value=''),
            'choix_formation_commission_proximite': Mock(value=''),
            'choix_formation_date_admission': Mock(value=''),
            'projet_recherche_duree_prevue_realisation_doctorat': Mock(value=''),
            'projet_recherche_temps_consacre_these': Mock(value=''),
            'projet_recherche_sujet': Mock(value=''),
            'projet_recherche_sigle_institut_recherche': Mock(value=''),
            'projet_recherche_lieu_these': Mock(value=''),
            'cotutelle_cotutelle': Mock(value=''),
            'cotutelle_institution_fwb': Mock(value=''),
            'cotutelle_nom_etablissement': Mock(value=''),
            'formation_doctorale_colloques_conferences_ects': Mock(value=''),
            'formation_doctorale_communications_orales_hors_conf_ects': Mock(value=''),
            'formation_doctorale_seminaires_suivis_ects': Mock(value=''),
            'formation_doctorale_publications_ects': Mock(value=''),
            'formation_doctorale_services_ects': Mock(value=''),
            'formation_doctorale_sejours_recherche_ects': Mock(value=''),
            'formation_doctorale_vae_ects': Mock(value=''),
            'formation_doctorale_cours_formations_ecoles_ects': Mock(value=''),
            'formation_doctorale_epreuves_ects': Mock(value=''),
            'epreuve_confirmation_date_limite': Mock(value=''),
            'epreuve_confirmation_date_epreuve': Mock(value=''),
            'epreuve_confirmation_statut': Mock(value=''),
            'doctorate_errors': Mock(value=''),
        }

        self.doctorate_header_row = tuple(Mock(value=key) for key in self.doctorate_first_row_cells)
        self.doctorate_first_row = tuple(self.doctorate_first_row_cells.values())

        self.doctorate_rows = [
            self.doctorate_header_row,
            self.doctorate_first_row,
        ]

        self.doctorate_worksheet = MagicMock(
            iter_rows=partial(self.mock_iter_rows, current_list=self.doctorate_rows),
            cell=partial(self.mock_cell, current_list=self.doctorate_rows),
        )

        self.supervision_first_row_cells = {
            'noma_doctorant': Mock(value=''),
            'promoteur_ou_membre': Mock(value=''),
            'est_promoteur_reference': Mock(value=''),
            'prenom': Mock(value=''),
            'nom': Mock(value=''),
            'email': Mock(value=''),
            'doctorat_avec_these': Mock(value=''),
            'institution': Mock(value=''),
            'ville': Mock(value=''),
            'pays': Mock(value=''),
            'langue_contact': Mock(value=''),
            'supervision_errors': Mock(value=''),
        }

        self.first_row_cells = {
            **self.doctorate_first_row_cells,
            **self.supervision_first_row_cells,
        }

        self.supervision_header_row = tuple(Mock(value=key) for key in self.supervision_first_row_cells)
        self.supervision_first_row = tuple(self.supervision_first_row_cells.values())

        self.supervision_rows = [
            self.supervision_header_row,
            self.supervision_first_row,
        ]

        self.supervision_worksheet = MagicMock(
            iter_rows=partial(self.mock_iter_rows, current_list=self.supervision_rows),
            cell=partial(self.mock_cell, current_list=self.supervision_rows),
        )

        self.worksheets = [
            self.doctorate_worksheet,
            self.supervision_worksheet,
        ]

        self.workbook = MagicMock(worksheets=self.worksheets)

        excel_patcher = mock.patch(
            'parcours_doctoral.views.config.doctorate_import_from_xlsx.load_workbook',
            side_effect=lambda **kwargs: self.workbook,
        )
        self.excel_patched = excel_patcher.start()
        self.addCleanup(excel_patcher.stop)

    def test_with_no_file(self):
        self.client.force_login(user=self.fac_manager_user)

        response = self.client.post(path=self.url, data={})

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('file'))

    def _post_request(self):
        return self.client.post(
            path=self.url,
            data={'file': self.get_example_file()},
        )

    def test_with_worksheets_number_different_than_two(self):
        self.client.force_login(user=self.fac_manager_user)

        self.workbook.worksheets = []

        response = self._post_request()

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn(gettext_lazy('The file must have %(nb)s worksheets.') % {'nb': 2}, form.errors.get('file'))

        self.workbook.worksheets = [
            self.doctorate_worksheet,
            self.doctorate_worksheet,
            self.doctorate_worksheet,
        ]

        response = self._post_request()

        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertIn(gettext_lazy('The file must have %(nb)s worksheets.') % {'nb': 2}, form.errors.get('file'))

    def assertFieldIsValid(self, field_name, field_value):
        self.first_row_cells[field_name].value = field_value
        self._post_request()
        self.assertIsNone(self.first_row_cells[field_name].comment)

    def assertFieldIsInvalid(self, field_name, field_value, error):
        self.first_row_cells[field_name].value = field_value
        self._post_request()
        self.assertEqual(self.first_row_cells[field_name].comment.errors_types, [error])

    def test_doctorate_import_with_noma(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='identification_noma',
            field_value=None,
            error='string_type',
        )

        self.assertFieldIsInvalid(
            field_name='identification_noma',
            field_value='0123456',
            error='string_pattern_mismatch',
        )

        self.assertFieldIsInvalid(
            field_name='identification_noma',
            field_value='01234568',
            error='foreign_key_value_error',
        )

        self.assertFieldIsValid(
            field_name='identification_noma',
            field_value=self.student.registration_id,
        )

    def test_doctorate_import_with_student_name(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='identification_nom_etudiant',
            field_value=None,
            error='string_type',
        )

        self.assertFieldIsValid(
            field_name='identification_nom_etudiant',
            field_value='John Doe',
        )

    def test_doctorate_import_with_admission_type(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='choix_formation_admission_preadmission',
            field_value=None,
            error='literal_error',
        )

        self.assertFieldIsInvalid(
            field_name='choix_formation_admission_preadmission',
            field_value='ABCDEF',
            error='literal_error',
        )

        self.assertFieldIsValid(
            field_name='choix_formation_admission_preadmission',
            field_value='ADMISSION',
        )

    def test_doctorate_import_with_sector_name(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='choix_formation_secteur',
            field_value=None,
            error='string_type',
        )

        self.assertFieldIsValid(
            field_name='choix_formation_secteur',
            field_value='SST',
        )

    def test_doctorate_import_with_training_acronym(self):
        self.client.force_login(user=self.fac_manager_user)

        self.doctorate_first_row_cells['identification_noma'].value = self.student.registration_id

        self.assertFieldIsInvalid(
            field_name='choix_formation_sigle_doctorat',
            field_value=None,
            error='string_type',
        )

        self.assertFieldIsInvalid(
            field_name='choix_formation_sigle_doctorat',
            field_value='01234568',
            error='foreign_key_value_error',
        )

        self.assertFieldIsInvalid(
            field_name='choix_formation_sigle_doctorat',
            field_value=self.training.acronym,
            error='invalid_enrolment',
        )

        InscriptionProgrammeAnnuelFactory(
            programme_cycle__etudiant=self.student,
            programme__offer=self.training,
        )

        self.assertFieldIsValid(
            field_name='choix_formation_sigle_doctorat',
            field_value=self.training.acronym,
        )

    def test_doctorate_import_with_proximity_commission(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='choix_formation_commission_proximite',
            field_value=None,
            error='literal_error',
        )

        self.assertFieldIsInvalid(
            field_name='choix_formation_commission_proximite',
            field_value='ABCDEF',
            error='literal_error',
        )

        self.assertFieldIsValid(
            field_name='choix_formation_commission_proximite',
            field_value='ECONOMY',
        )

    def test_doctorate_import_with_admission_date(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='choix_formation_date_admission',
            field_value=None,
            error='date_type',
        )

        self.assertFieldIsInvalid(
            field_name='choix_formation_date_admission',
            field_value='2020-13-31',
            error='date_from_datetime_parsing',
        )

        self.assertFieldIsValid(
            field_name='choix_formation_date_admission',
            field_value=datetime.date(2020, 12, 31),
        )

        self.assertFieldIsValid(
            field_name='choix_formation_date_admission',
            field_value='2020-12-31',
        )

    def test_doctorate_import_with_doctorate_planned_duration(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='projet_recherche_duree_prevue_realisation_doctorat',
            field_value=None,
            error='int_type',
        )

        self.assertFieldIsInvalid(
            field_name='projet_recherche_duree_prevue_realisation_doctorat',
            field_value=-1,
            error='greater_than_equal',
        )

        self.assertFieldIsInvalid(
            field_name='projet_recherche_duree_prevue_realisation_doctorat',
            field_value=201,
            error='less_than_equal',
        )

        self.assertFieldIsValid(
            field_name='projet_recherche_duree_prevue_realisation_doctorat',
            field_value=0,
        )

        self.assertFieldIsValid(
            field_name='projet_recherche_duree_prevue_realisation_doctorat',
            field_value=200,
        )

    def test_doctorate_import_with_thesis_dedicated_time(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='projet_recherche_temps_consacre_these',
            field_value=None,
            error='int_type',
        )

        self.assertFieldIsInvalid(
            field_name='projet_recherche_temps_consacre_these',
            field_value=-1,
            error='greater_than_equal',
        )

        self.assertFieldIsInvalid(
            field_name='projet_recherche_temps_consacre_these',
            field_value=101,
            error='less_than_equal',
        )

        self.assertFieldIsValid(
            field_name='projet_recherche_temps_consacre_these',
            field_value=0,
        )

        self.assertFieldIsValid(
            field_name='projet_recherche_temps_consacre_these',
            field_value=100,
        )

    def test_doctorate_import_with_project_subject(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='projet_recherche_sujet',
            field_value=None,
            error='string_type',
        )

        self.assertFieldIsInvalid(
            field_name='projet_recherche_sujet',
            field_value='A' * 1024,
            error='string_too_long',
        )

        self.assertFieldIsValid(
            field_name='projet_recherche_sujet',
            field_value='A' * 1023,
        )

    def test_doctorate_import_with_thesis_institute_acronym(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='projet_recherche_sigle_institut_recherche',
            field_value=None,
            error='string_type',
        )

        self.assertFieldIsInvalid(
            field_name='projet_recherche_sigle_institut_recherche',
            field_value='01234568',
            error='foreign_key_value_error',
        )

        self.assertFieldIsValid(
            field_name='projet_recherche_sigle_institut_recherche',
            field_value=self.commission_version.acronym,
        )

    def test_doctorate_import_with_thesis_location(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='projet_recherche_lieu_these',
            field_value=None,
            error='string_type',
        )

        self.assertFieldIsInvalid(
            field_name='projet_recherche_lieu_these',
            field_value='A' * 256,
            error='string_too_long',
        )

        self.assertFieldIsValid(
            field_name='projet_recherche_lieu_these',
            field_value='A' * 255,
        )

    def test_doctorate_import_with_cotutelle(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='cotutelle_cotutelle',
            field_value=None,
            error='enum',
        )

        self.assertFieldIsInvalid(
            field_name='cotutelle_cotutelle',
            field_value='ok',
            error='enum',
        )

        self.assertFieldIsValid(
            field_name='cotutelle_cotutelle',
            field_value=ChoixOuiNon.OUI.value,
        )

    def test_doctorate_import_with_cotutelle_fwb_institute(self):
        self.client.force_login(user=self.fac_manager_user)

        self.doctorate_first_row_cells['cotutelle_cotutelle'].value = ChoixOuiNon.OUI.value

        self.assertFieldIsInvalid(
            field_name='cotutelle_institution_fwb',
            field_value=None,
            error='cotutelle_data_error',
        )

        self.assertFieldIsInvalid(
            field_name='cotutelle_institution_fwb',
            field_value='0123456',
            error='enum',
        )

        self.assertFieldIsValid(
            field_name='cotutelle_institution_fwb',
            field_value=ChoixOuiNon.OUI.value,
        )

        self.doctorate_first_row_cells['cotutelle_cotutelle'].value = ChoixOuiNon.NON.value

        self.assertFieldIsValid(
            field_name='cotutelle_institution_fwb',
            field_value=None,
        )

    def test_doctorate_import_with_cotutelle_institute_name(self):
        self.client.force_login(user=self.fac_manager_user)

        self.doctorate_first_row_cells['cotutelle_cotutelle'].value = ChoixOuiNon.OUI.value

        self.assertFieldIsInvalid(
            field_name='cotutelle_nom_etablissement',
            field_value=None,
            error='cotutelle_data_error',
        )

        self.assertFieldIsInvalid(
            field_name='cotutelle_nom_etablissement',
            field_value='A' * 256,
            error='string_too_long',
        )

        self.assertFieldIsValid(
            field_name='cotutelle_nom_etablissement',
            field_value='A' * 255,
        )

        self.doctorate_first_row_cells['cotutelle_cotutelle'].value = ChoixOuiNon.NON.value

        self.assertFieldIsValid(
            field_name='cotutelle_nom_etablissement',
            field_value=None,
        )

    def test_doctorate_import_with_activities_ects(self):
        self.client.force_login(user=self.fac_manager_user)

        for field in [
            'formation_doctorale_colloques_conferences_ects',
            'formation_doctorale_communications_orales_hors_conf_ects',
            'formation_doctorale_seminaires_suivis_ects',
            'formation_doctorale_publications_ects',
            'formation_doctorale_services_ects',
            'formation_doctorale_sejours_recherche_ects',
            'formation_doctorale_vae_ects',
            'formation_doctorale_cours_formations_ecoles_ects',
            'formation_doctorale_epreuves_ects',
        ]:
            self.assertFieldIsInvalid(
                field_name=field,
                field_value=None,
                error='decimal_type',
            )

            self.assertFieldIsInvalid(
                field_name=field,
                field_value='100.1',
                error='decimal_max_digits',
            )

            self.assertFieldIsInvalid(
                field_name=field,
                field_value='10.11',
                error='decimal_max_digits',
            )

            self.assertFieldIsInvalid(
                field_name=field,
                field_value=-1,
                error='greater_than_equal',
            )

            self.assertFieldIsValid(
                field_name=field,
                field_value='55.5',
            )

            self.assertFieldIsValid(
                field_name=field,
                field_value=10,
            )

            self.assertFieldIsValid(
                field_name=field,
                field_value=Decimal('10.2'),
            )

    def test_doctorate_import_with_confirmation_deadline(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='epreuve_confirmation_date_limite',
            field_value=True,
            error='date_type',
        )

        self.assertFieldIsInvalid(
            field_name='epreuve_confirmation_date_limite',
            field_value='2020-13-31',
            error='date_from_datetime_parsing',
        )

        self.assertFieldIsValid(
            field_name='epreuve_confirmation_date_limite',
            field_value=None,
        )

        self.assertFieldIsValid(
            field_name='epreuve_confirmation_date_limite',
            field_value='2020-12-31',
        )

        self.assertFieldIsValid(
            field_name='epreuve_confirmation_date_limite',
            field_value=datetime.date(2020, 12, 31),
        )

    def test_doctorate_import_with_confirmation_date(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='epreuve_confirmation_date_epreuve',
            field_value=True,
            error='date_type',
        )

        self.assertFieldIsInvalid(
            field_name='epreuve_confirmation_date_epreuve',
            field_value='2020-13-31',
            error='date_from_datetime_parsing',
        )

        self.assertFieldIsValid(
            field_name='epreuve_confirmation_date_epreuve',
            field_value=None,
        )

        self.assertFieldIsValid(
            field_name='epreuve_confirmation_date_epreuve',
            field_value='2020-12-31',
        )

        self.assertFieldIsValid(
            field_name='epreuve_confirmation_date_epreuve',
            field_value=datetime.date(2020, 12, 31),
        )

    def test_doctorate_import_with_confirmation_status(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='epreuve_confirmation_statut',
            field_value=None,
            error='literal_error',
        )

        self.assertFieldIsInvalid(
            field_name='epreuve_confirmation_statut',
            field_value='ABCDEF',
            error='literal_error',
        )

        self.assertFieldIsValid(
            field_name='epreuve_confirmation_statut',
            field_value='CONFIRMATION_REUSSIE',
        )

    def test_supervision_import_with_noma(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='noma_doctorant',
            field_value=None,
            error='string_type',
        )

        self.assertFieldIsInvalid(
            field_name='noma_doctorant',
            field_value='0123456',
            error='string_pattern_mismatch',
        )

        self.assertFieldIsInvalid(
            field_name='noma_doctorant',
            field_value='01234568',
            error='foreign_key_value_error',
        )

        # The following error is invalid because there is no matching row in the first worksheet
        self.assertFieldIsInvalid(
            field_name='noma_doctorant',
            field_value=self.student.registration_id,
            error='foreign_key_value_error',
        )

        self.doctorate_first_row_cells['identification_noma'].value = self.student.registration_id

        self.assertFieldIsValid(
            field_name='noma_doctorant',
            field_value=self.student.registration_id,
        )

    def test_supervision_import_with_actor_type(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='promoteur_ou_membre',
            field_value=None,
            error='literal_error',
        )

        self.assertFieldIsInvalid(
            field_name='promoteur_ou_membre',
            field_value='ABCDEF',
            error='literal_error',
        )

        self.assertFieldIsValid(
            field_name='promoteur_ou_membre',
            field_value='PROMOTER',
        )

    def test_supervision_import_with_lead_actor(self):
        self.client.force_login(user=self.fac_manager_user)

        self.supervision_first_row_cells['promoteur_ou_membre'].value = 'PROMOTER'

        self.assertFieldIsInvalid(
            field_name='est_promoteur_reference',
            field_value=None,
            error='enum',
        )

        self.assertFieldIsInvalid(
            field_name='est_promoteur_reference',
            field_value='ABCDEF',
            error='enum',
        )

        self.assertFieldIsValid(
            field_name='est_promoteur_reference',
            field_value=ChoixOuiNon.OUI.value,
        )

        self.supervision_first_row_cells['promoteur_ou_membre'].value = 'CA_MEMBER'

        self.assertFieldIsInvalid(
            field_name='est_promoteur_reference',
            field_value=ChoixOuiNon.OUI.value,
            error='promoter_data_error',
        )

        self.assertFieldIsValid(
            field_name='est_promoteur_reference',
            field_value=ChoixOuiNon.NON.value,
        )

    def test_supervision_import_with_actor_first_name(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='prenom',
            field_value=None,
            error='string_type',
        )

        self.assertFieldIsInvalid(
            field_name='prenom',
            field_value='A' * 51,
            error='string_too_long',
        )

        self.assertFieldIsValid(
            field_name='prenom',
            field_value='A' * 50,
        )

    def test_supervision_import_with_actor_last_name(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='nom',
            field_value=None,
            error='string_type',
        )

        self.assertFieldIsInvalid(
            field_name='nom',
            field_value='A' * 51,
            error='string_too_long',
        )

        self.assertFieldIsValid(
            field_name='nom',
            field_value='A' * 50,
        )

    def test_supervision_import_with_actor_email(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='email',
            field_value=None,
            error='string_type',
        )

        self.assertFieldIsInvalid(
            field_name='email',
            field_value='A' * 256,
            error='string_too_long',
        )

        self.assertFieldIsValid(
            field_name='email',
            field_value='A' * 255,
        )

    def test_supervision_import_with_actor_title(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='doctorat_avec_these',
            field_value='ok',
            error='enum',
        )

        self.assertFieldIsValid(
            field_name='doctorat_avec_these',
            field_value=ChoixOuiNon.OUI.value,
        )

        # This is an external promoter so the field is required
        self.assertFieldIsInvalid(
            field_name='doctorat_avec_these',
            field_value=None,
            error='external_promoter_data_error',
        )

        self.supervision_first_row_cells['email'].value = self.external_person.email

        self.assertFieldIsInvalid(
            field_name='doctorat_avec_these',
            field_value=None,
            error='external_promoter_data_error',
        )

        self.supervision_first_row_cells['email'].value = self.internal_student_not_tutor.email

        self.assertFieldIsInvalid(
            field_name='doctorat_avec_these',
            field_value=None,
            error='external_promoter_data_error',
        )

        # This is an internal promoter so the field is not required
        self.supervision_first_row_cells['email'].value = self.internal_student_and_tutor.email

        self.assertFieldIsValid(
            field_name='doctorat_avec_these',
            field_value=None,
        )

        self.supervision_first_row_cells['email'].value = self.internal_person.email

        self.assertFieldIsValid(
            field_name='doctorat_avec_these',
            field_value=None,
        )

    def test_supervision_import_with_actor_institution(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='institution',
            field_value=10,
            error='string_type',
        )

        self.assertFieldIsInvalid(
            field_name='institution',
            field_value='A' * 256,
            error='string_too_long',
        )

        self.assertFieldIsValid(
            field_name='institution',
            field_value='A' * 255,
        )

        # This is an external promoter so the field is required
        self.supervision_first_row_cells['email'].value = self.external_person.email

        self.assertFieldIsInvalid(
            field_name='institution',
            field_value=None,
            error='external_promoter_data_error',
        )

        # This is an internal promoter so the field is not required
        self.supervision_first_row_cells['email'].value = self.internal_person.email

        self.assertFieldIsValid(
            field_name='institution',
            field_value=None,
        )

    def test_supervision_import_with_actor_city(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='ville',
            field_value=10,
            error='string_type',
        )

        self.assertFieldIsInvalid(
            field_name='ville',
            field_value='A' * 256,
            error='string_too_long',
        )

        self.assertFieldIsValid(
            field_name='ville',
            field_value='A' * 255,
        )

        # This is an external promoter so the field is required
        self.supervision_first_row_cells['email'].value = self.external_person.email

        self.assertFieldIsInvalid(
            field_name='ville',
            field_value=None,
            error='external_promoter_data_error',
        )

        # This is an internal promoter so the field is not required
        self.supervision_first_row_cells['email'].value = self.internal_person.email

        self.assertFieldIsValid(
            field_name='ville',
            field_value=None,
        )

    def test_supervision_import_with_actor_country(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='pays',
            field_value=10,
            error='string_type',
        )

        self.assertFieldIsInvalid(
            field_name='pays',
            field_value='ABCDE',
            error='foreign_key_value_error',
        )

        self.assertFieldIsValid(
            field_name='pays',
            field_value=self.country.iso_code,
        )

        # This is an external promoter so the field is required
        self.supervision_first_row_cells['email'].value = self.external_person.email

        self.assertFieldIsInvalid(
            field_name='pays',
            field_value=None,
            error='external_promoter_data_error',
        )

        # This is an internal promoter so the field is not required
        self.supervision_first_row_cells['email'].value = self.internal_person.email

        self.assertFieldIsValid(
            field_name='pays',
            field_value=None,
        )

    def test_supervision_import_with_actor_contact_language(self):
        self.client.force_login(user=self.fac_manager_user)

        self.assertFieldIsInvalid(
            field_name='langue_contact',
            field_value=10,
            error='literal_error',
        )

        self.assertFieldIsInvalid(
            field_name='langue_contact',
            field_value='ABCDE',
            error='literal_error',
        )

        self.assertFieldIsValid(
            field_name='langue_contact',
            field_value=settings.LANGUAGE_CODE_FR,
        )

        # This is an external promoter so the field is required
        self.supervision_first_row_cells['email'].value = self.external_person.email

        self.assertFieldIsInvalid(
            field_name='langue_contact',
            field_value=None,
            error='external_promoter_data_error',
        )

        # This is an internal promoter so the field is not required
        self.supervision_first_row_cells['email'].value = self.internal_person.email

        self.assertFieldIsValid(
            field_name='langue_contact',
            field_value=None,
        )

    def test_with_duplicate_doctorate_rows(self):
        self.client.force_login(user=self.fac_manager_user)

        self.doctorate_rows.append(deepcopy(self.doctorate_first_row))

        response = self._post_request()

        self.assertEqual(response.status_code, 200)

        first_row_errors = self.doctorate_rows[1][-1].value
        second_row_errors = self.doctorate_rows[2][-1].value

        self.assertIn('A row with the same identifier has already been encountered.', first_row_errors)
        self.assertIn('A row with the same identifier has already been encountered.', second_row_errors)

    def test_with_duplicate_supervision_rows(self):
        self.client.force_login(user=self.fac_manager_user)

        self.doctorate_first_row_cells['identification_noma'].value = self.student.registration_id
        self.supervision_first_row_cells['noma_doctorant'].value = self.student.registration_id
        self.supervision_first_row_cells['email'].value = self.internal_person.email

        self.supervision_rows.append(deepcopy(self.supervision_first_row))

        response = self._post_request()

        self.assertEqual(response.status_code, 200)

        first_row_errors = self.supervision_rows[1][-1].value
        second_row_errors = self.supervision_rows[2][-1].value

        self.assertIn('A row with the same identifier has already been encountered.', first_row_errors)
        self.assertIn('A row with the same identifier has already been encountered.', second_row_errors)

    def test_with_no_lead_actor(self):
        self.client.force_login(user=self.fac_manager_user)

        self.doctorate_first_row_cells['identification_noma'].value = self.student.registration_id
        self.supervision_first_row_cells['noma_doctorant'].value = self.student.registration_id
        self.supervision_first_row_cells['email'].value = self.internal_person.email

        response = self._post_request()

        self.assertEqual(response.status_code, 200)

        first_row_errors = self.supervision_rows[1][-1].value

        self.assertIn('One contact supervisor must be selected for each doctorate.', first_row_errors)

    def test_with_several_lead_actors(self):
        self.client.force_login(user=self.fac_manager_user)

        self.doctorate_first_row_cells['identification_noma'].value = self.student.registration_id
        self.supervision_first_row_cells['noma_doctorant'].value = self.student.registration_id
        self.supervision_first_row_cells['email'].value = self.internal_person.email
        self.supervision_first_row_cells['est_promoteur_reference'].value = ChoixOuiNon.OUI.value

        self.supervision_rows.append(deepcopy(self.supervision_first_row))

        response = self._post_request()

        self.assertEqual(response.status_code, 200)

        first_row_errors = self.supervision_rows[1][-1].value
        second_row_errors = self.supervision_rows[2][-1].value

        self.assertIn('There is too much contact supervisors for this doctorate.', first_row_errors)
        self.assertIn('There is too much contact supervisors for this doctorate.', second_row_errors)

    def test_import_valid_data(self):
        self.client.force_login(user=self.fac_manager_user)

        InscriptionProgrammeAnnuelFactory(
            programme_cycle__etudiant=self.student,
            programme__offer=self.training,
        )

        self.doctorate_first_row_cells['identification_noma'].value = self.student.registration_id
        self.doctorate_first_row_cells['identification_nom_etudiant'].value = self.student.person.last_name
        self.doctorate_first_row_cells['choix_formation_admission_preadmission'].value = 'ADMISSION'
        self.doctorate_first_row_cells['choix_formation_secteur'].value = 'SST'
        self.doctorate_first_row_cells['choix_formation_sigle_doctorat'].value = self.training.acronym
        self.doctorate_first_row_cells['choix_formation_commission_proximite'].value = 'PHYSICS'
        self.doctorate_first_row_cells['choix_formation_date_admission'].value = datetime.date(2025, 12, 31)
        self.doctorate_first_row_cells['projet_recherche_duree_prevue_realisation_doctorat'].value = 150
        self.doctorate_first_row_cells['projet_recherche_temps_consacre_these'].value = 80
        self.doctorate_first_row_cells['projet_recherche_sujet'].value = 'Subject'
        self.doctorate_first_row_cells[
            'projet_recherche_sigle_institut_recherche'
        ].value = self.commission_version.acronym
        self.doctorate_first_row_cells['projet_recherche_lieu_these'].value = 'Louvain-La-Neuve'
        self.doctorate_first_row_cells['cotutelle_cotutelle'].value = ChoixOuiNon.OUI.value
        self.doctorate_first_row_cells['cotutelle_institution_fwb'].value = ChoixOuiNon.OUI.value
        self.doctorate_first_row_cells['cotutelle_nom_etablissement'].value = 'ULB'
        self.doctorate_first_row_cells['formation_doctorale_colloques_conferences_ects'].value = 1
        self.doctorate_first_row_cells['formation_doctorale_communications_orales_hors_conf_ects'].value = 2
        self.doctorate_first_row_cells['formation_doctorale_seminaires_suivis_ects'].value = 3
        self.doctorate_first_row_cells['formation_doctorale_publications_ects'].value = 4
        self.doctorate_first_row_cells['formation_doctorale_services_ects'].value = 5
        self.doctorate_first_row_cells['formation_doctorale_sejours_recherche_ects'].value = 6
        self.doctorate_first_row_cells['formation_doctorale_vae_ects'].value = 7
        self.doctorate_first_row_cells['formation_doctorale_cours_formations_ecoles_ects'].value = 8
        self.doctorate_first_row_cells['formation_doctorale_epreuves_ects'].value = 9
        self.doctorate_first_row_cells['epreuve_confirmation_date_limite'].value = datetime.date(2026, 9, 30)
        self.doctorate_first_row_cells['epreuve_confirmation_date_epreuve'].value = datetime.date(2026, 8, 31)
        self.doctorate_first_row_cells[
            'epreuve_confirmation_statut'
        ].value = ChoixStatutParcoursDoctoral.CONFIRMATION_A_REPRESENTER.name

        self.supervision_first_row_cells['noma_doctorant'].value = self.student.registration_id
        self.supervision_first_row_cells['promoteur_ou_membre'].value = 'PROMOTER'
        self.supervision_first_row_cells['est_promoteur_reference'].value = ChoixOuiNon.NON.value
        self.supervision_first_row_cells['prenom'].value = 'John'
        self.supervision_first_row_cells['nom'].value = 'Doe'
        self.supervision_first_row_cells['email'].value = 'john.doe@address.be'
        self.supervision_first_row_cells['doctorat_avec_these'].value = ChoixOuiNon.OUI.value
        self.supervision_first_row_cells['institution'].value = 'ULB'
        self.supervision_first_row_cells['ville'].value = 'Bruxelles'
        self.supervision_first_row_cells['pays'].value = self.country.iso_code
        self.supervision_first_row_cells['langue_contact'].value = settings.LANGUAGE_CODE_FR

        second_row_cells = {
            'noma_doctorant': Mock(value=self.student.registration_id),
            'promoteur_ou_membre': Mock(value='CA_MEMBER'),
            'est_promoteur_reference': Mock(value=ChoixOuiNon.NON.value),
            'prenom': Mock(value=self.internal_person.first_name),
            'nom': Mock(value=self.internal_person.last_name),
            'email': Mock(value=self.internal_person.email),
            'doctorat_avec_these': Mock(value=None),
            'institution': Mock(value=None),
            'ville': Mock(value=None),
            'pays': Mock(value=None),
            'langue_contact': Mock(value=None),
            'supervision_errors': Mock(value=''),
        }

        third_row_cells = {
            'noma_doctorant': Mock(value=self.student.registration_id),
            'promoteur_ou_membre': Mock(value='PROMOTER'),
            'est_promoteur_reference': Mock(value=ChoixOuiNon.OUI.value),
            'prenom': Mock(value=self.internal_student_and_tutor.last_name),
            'nom': Mock(value=self.internal_student_and_tutor.first_name),
            'email': Mock(value=self.internal_student_and_tutor.email),
            'doctorat_avec_these': Mock(value=None),
            'institution': Mock(value=None),
            'ville': Mock(value=None),
            'pays': Mock(value=None),
            'langue_contact': Mock(value=None),
            'supervision_errors': Mock(value=''),
        }

        self.supervision_rows.append(tuple(second_row_cells.values()))
        self.supervision_rows.append(tuple(third_row_cells.values()))

        response = self._post_request()

        self.assertRedirects(response, expected_url=self.url)

        # Check that the data have been added

        # The doctorate
        doctorates: QuerySet[ParcoursDoctoral] = ParcoursDoctoral.objects.all()

        self.assertEqual(len(doctorates), 1)

        doctorate = doctorates[0]

        self.assertEqual(doctorate.student, self.student.person)
        self.assertEqual(doctorate.admission_type, ChoixTypeAdmission.ADMISSION.name)
        self.assertEqual(doctorate.training, self.training)
        self.assertEqual(doctorate.proximity_commission, ChoixSousDomaineSciences.PHYSICS.name)
        self.assertEqual(doctorate.admission_approved_by_cdd_at, datetime.datetime(2025, 12, 31))
        self.assertEqual(doctorate.planned_duration, 150)
        self.assertEqual(doctorate.dedicated_time, 80)
        self.assertEqual(doctorate.project_title, 'Subject')
        self.assertEqual(doctorate.thesis_institute, self.commission_version)
        self.assertEqual(doctorate.thesis_location, 'Louvain-La-Neuve')
        self.assertEqual(doctorate.cotutelle, True)
        self.assertEqual(doctorate.cotutelle_institution_fwb, True)
        self.assertEqual(doctorate.cotutelle_other_institution_name, 'ULB')
        self.assertEqual(doctorate.status, ChoixStatutParcoursDoctoral.CONFIRMATION_A_REPRESENTER.name)

        # The activities
        activities: QuerySet[Activity] = Activity.objects.filter(parcours_doctoral=doctorate)

        created_activities_categories = CategorieActivite.get_names_except(CategorieActivite.UCL_COURSE)

        self.assertEqual(len(activities), len(created_activities_categories))

        activities_by_category = {activity.category: activity for activity in activities}

        for index, category in enumerate(created_activities_categories, start=1):
            activity = activities_by_category.get(category)
            self.assertIsNotNone(activity)
            self.assertEqual(activity.context, ContexteFormation.DOCTORAL_TRAINING.name)
            self.assertEqual(activity.category, category)
            self.assertEqual(activity.ects, index)

        # The confirmation paper
        confirmation_papers = ConfirmationPaper.objects.all()

        self.assertEqual(len(confirmation_papers), 1)

        confirmation_paper = confirmation_papers[0]

        self.assertEqual(confirmation_paper.confirmation_deadline, datetime.date(2026, 9, 30))
        self.assertEqual(confirmation_paper.confirmation_date, datetime.date(2026, 8, 31))

        # The supervision group
        self.assertIsNotNone(doctorate.supervision_group)

        actors: QuerySet[ParcoursDoctoralSupervisionActor] = ParcoursDoctoralSupervisionActor.objects.all()

        self.assertEqual(len(actors), 3)

        external_promoter = next((a for a in actors if a.is_external), None)

        self.assertIsNotNone(external_promoter)

        self.assertEqual(external_promoter.type, ActorType.PROMOTER.name)
        self.assertEqual(external_promoter.person, None)
        self.assertEqual(external_promoter.first_name, 'John')
        self.assertEqual(external_promoter.last_name, 'Doe')
        self.assertEqual(external_promoter.email, 'john.doe@address.be')
        self.assertEqual(external_promoter.is_doctor, True)
        self.assertEqual(external_promoter.institute, 'ULB')
        self.assertEqual(external_promoter.city, 'Bruxelles')
        self.assertEqual(external_promoter.country, self.country)
        self.assertEqual(external_promoter.language, settings.LANGUAGE_CODE_FR)
        self.assertEqual(external_promoter.is_reference_promoter, False)
        self.assertEqual(external_promoter.state, SignatureState.APPROVED.name)

        internal_promoter = next((a for a in actors if not a.is_external and a.type == 'PROMOTER'), None)

        self.assertIsNotNone(internal_promoter)

        self.assertEqual(internal_promoter.type, ActorType.PROMOTER.name)
        self.assertEqual(internal_promoter.person, self.internal_student_and_tutor)
        self.assertEqual(internal_promoter.is_reference_promoter, True)
        self.assertEqual(internal_promoter.state, SignatureState.APPROVED.name)

        internal_ca_member = next((a for a in actors if not a.is_external and a.type == 'CA_MEMBER'), None)

        self.assertIsNotNone(internal_ca_member)

        self.assertEqual(internal_ca_member.type, ActorType.CA_MEMBER.name)
        self.assertEqual(internal_ca_member.person, self.internal_person)
        self.assertEqual(internal_ca_member.is_reference_promoter, False)
        self.assertEqual(internal_ca_member.state, SignatureState.APPROVED.name)

        promoters_roles = Promoter.objects.all()
        self.assertEqual(len(promoters_roles), 1)
        self.assertEqual(promoters_roles[0].person, internal_promoter.person)

        committee_members_roles = CommitteeMember.objects.all()
        self.assertEqual(len(committee_members_roles), 1)
        self.assertEqual(committee_members_roles[0].person, internal_ca_member.person)
