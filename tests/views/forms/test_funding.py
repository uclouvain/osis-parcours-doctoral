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
import uuid
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import (
    ENTITY_CDE,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixTypeAdmission,
    ChoixTypeContratTravail,
)
from admission.tests.factories import DoctorateAdmissionFactory
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from parcours_doctoral.ddd.domain.model.enums import ChoixTypeFinancement
from parcours_doctoral.models import ParcoursDoctoral
from parcours_doctoral.tests.factories.parcours_doctoral import (
    FormationFactory,
    ParcoursDoctoralFactory,
)
from reference.tests.factories.scholarship import DoctorateScholarshipFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class FundingFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)

        cls.organization = EntityVersionFactory().entity.organization
        cls.other_organization = EntityVersionFactory().entity.organization

        cls.scholarship = DoctorateScholarshipFactory()
        cls.other_scholarship = DoctorateScholarshipFactory()

        cls.training = FormationFactory(
            management_entity=first_doctoral_commission,
            academic_year=academic_years[0],
        )

        cls.manager = ProgramManagerFactory(education_group=cls.training.education_group).person

        cls.other_manager = ProgramManagerFactory().person

        cls.admission = DoctorateAdmissionFactory(
            training=cls.training,
            type=ChoixTypeAdmission.ADMISSION.name,
        )

        cls.pre_admission = DoctorateAdmissionFactory(
            training=cls.training, type=ChoixTypeAdmission.PRE_ADMISSION.name, candidate=cls.admission.candidate
        )

    def setUp(self):
        # Mock documents
        patcher = patch("osis_document_components.services.get_remote_token", side_effect=lambda value, **kwargs: value)
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document_components.services.get_remote_metadata",
            return_value={"name": "myfile", "mimetype": "application/pdf", "size": 1},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document_components.services.confirm_remote_upload",
            side_effect=lambda token, *args, **kwargs: token,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch(
            "osis_document_components.fields.FileField._confirm_multiple_upload",
            side_effect=lambda _, value, __: value,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        self.doctorate: ParcoursDoctoral = ParcoursDoctoralFactory(
            training=self.training,
            student=self.admission.candidate,
            financing_type=ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
            other_international_scholarship='Other scholarship',
            international_scholarship=self.scholarship,
            financing_work_contract=ChoixTypeContratTravail.UCLOUVAIN_SCIENTIFIC_STAFF.name,
            financing_eft=10,
            scholarship_start_date=datetime.date(2022, 1, 1),
            scholarship_end_date=datetime.date(2024, 1, 1),
            scholarship_proof=[uuid.uuid4()],
            planned_duration=20,
            dedicated_time=30,
            is_fnrs_fria_fresh_csc_linked=True,
            financing_comment='Custom comment',
        )

        self.url = reverse('parcours_doctoral:update:funding', kwargs={'uuid': self.doctorate.uuid})

        self.default_data = {
            'type': '',
            'type_contrat_travail': ChoixTypeContratTravail.OTHER.name,
            'eft': 15,
            'bourse_recherche': self.other_scholarship.uuid,
            'autre_bourse_recherche': 'New other scholarship',
            'bourse_date_debut': datetime.date(2022, 2, 2),
            'bourse_date_fin': datetime.date(2024, 2, 2),
            'bourse_preuve_0': [uuid.uuid4()],
            'duree_prevue': 25,
            'temps_consacre': 35,
            'est_lie_fnrs_fria_fresh_csc': False,
            'commentaire': 'New custom comment',
        }

    def test_with_other_manager(self):
        self.client.force_login(user=self.other_manager.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_form_initialization_for_an_admission(self):
        self.client.force_login(user=self.manager.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertEqual(form['type'].value(), self.doctorate.financing_type)
        self.assertEqual(form['type_contrat_travail'].value(), self.doctorate.financing_work_contract)
        self.assertEqual(form['eft'].value(), self.doctorate.financing_eft)
        self.assertEqual(form['bourse_recherche'].value(), str(self.doctorate.international_scholarship.uuid))
        self.assertEqual(form['autre_bourse_recherche'].value(), self.doctorate.other_international_scholarship)
        self.assertEqual(form['bourse_date_debut'].value(), self.doctorate.scholarship_start_date)
        self.assertEqual(form['bourse_date_fin'].value(), self.doctorate.scholarship_end_date)
        self.assertEqual(form['bourse_preuve'].value(), self.doctorate.scholarship_proof)
        self.assertEqual(form['duree_prevue'].value(), self.doctorate.planned_duration)
        self.assertEqual(form['temps_consacre'].value(), self.doctorate.dedicated_time)
        self.assertEqual(form['est_lie_fnrs_fria_fresh_csc'].value(), self.doctorate.is_fnrs_fria_fresh_csc_linked)
        self.assertEqual(form['commentaire'].value(), self.doctorate.financing_comment)

        for field in [
            'type',
            'type_contrat_travail',
            'eft',
            'bourse_recherche',
            'autre_bourse_recherche',
            'bourse_date_debut',
            'bourse_date_fin',
            'bourse_preuve',
            'duree_prevue',
            'temps_consacre',
            'est_lie_fnrs_fria_fresh_csc',
        ]:
            self.assertEqual(form.label_classes.get(field), 'required_text', field)

        for field in [
            'commentaire',
        ]:
            self.assertEqual(form.label_classes.get(field), None, field)

    def test_form_initialization_for_a_pre_admission(self):
        self.client.force_login(user=self.manager.user)

        self.doctorate.admission_type = self.pre_admission.type
        self.doctorate.admission_approved_by_cdd_at = self.pre_admission.approved_by_cdd_at
        self.doctorate.save(update_fields=['admission', 'admission_type', 'admission_approved_by_cdd_at'])

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertEqual(form['type'].value(), self.doctorate.financing_type)
        self.assertEqual(form['type_contrat_travail'].value(), self.doctorate.financing_work_contract)
        self.assertEqual(form['eft'].value(), self.doctorate.financing_eft)
        self.assertEqual(form['bourse_recherche'].value(), str(self.doctorate.international_scholarship.uuid))
        self.assertEqual(form['autre_bourse_recherche'].value(), self.doctorate.other_international_scholarship)
        self.assertEqual(form['bourse_date_debut'].value(), self.doctorate.scholarship_start_date)
        self.assertEqual(form['bourse_date_fin'].value(), self.doctorate.scholarship_end_date)
        self.assertEqual(form['bourse_preuve'].value(), self.doctorate.scholarship_proof)
        self.assertEqual(form['duree_prevue'].value(), self.doctorate.planned_duration)
        self.assertEqual(form['temps_consacre'].value(), self.doctorate.dedicated_time)
        self.assertEqual(form['est_lie_fnrs_fria_fresh_csc'].value(), self.doctorate.is_fnrs_fria_fresh_csc_linked)
        self.assertEqual(form['commentaire'].value(), self.doctorate.financing_comment)

        for field in [
            'type_contrat_travail',
            'eft',
            'bourse_recherche',
            'autre_bourse_recherche',
        ]:
            self.assertEqual(form.label_classes.get(field), 'required_text', field)

        for field in [
            'commentaire',
            'type',
            'bourse_date_debut',
            'bourse_date_fin',
            'bourse_preuve',
            'duree_prevue',
            'temps_consacre',
            'est_lie_fnrs_fria_fresh_csc',
        ]:
            self.assertEqual(form.label_classes.get(field), None, field)

    def test_post_invalid_form_for_an_admission_without_data(self):
        self.client.force_login(self.manager.user)

        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(len(form.errors), 4)

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('type', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('duree_prevue', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('temps_consacre', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('est_lie_fnrs_fria_fresh_csc', []))

    def test_post_invalid_form_for_an_admission_and_a_work_contract(self):
        self.client.force_login(self.manager.user)

        response = self.client.post(
            self.url,
            {
                'type': ChoixTypeFinancement.WORK_CONTRACT.name,
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(len(form.errors), 5)

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('duree_prevue', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('temps_consacre', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('est_lie_fnrs_fria_fresh_csc', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('type_contrat_travail', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('eft', []))

    def test_post_invalid_form_for_an_admission_and_a_scholarship(self):
        self.client.force_login(self.manager.user)

        response = self.client.post(
            self.url,
            {
                'type': ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(len(form.errors), 8)

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('duree_prevue', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('temps_consacre', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('est_lie_fnrs_fria_fresh_csc', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('bourse_recherche', []))
        self.assertIn('', form.errors.get('autre_bourse_recherche', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('bourse_date_debut', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('bourse_date_fin', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('bourse_preuve', []))

    def test_post_invalid_form_for_an_admission_and_a_self_funding(self):
        self.client.force_login(self.manager.user)

        response = self.client.post(
            self.url,
            {
                'type': ChoixTypeFinancement.SELF_FUNDING.name,
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(len(form.errors), 3)

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('duree_prevue', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('temps_consacre', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('est_lie_fnrs_fria_fresh_csc', []))

    def test_post_invalid_form_for_a_pre_admission_and_a_work_contract(self):
        self.client.force_login(self.manager.user)

        self.doctorate.admission = self.pre_admission
        self.doctorate.admission_type = self.pre_admission.type
        self.doctorate.admission_approved_by_cdd_at = self.pre_admission.approved_by_cdd_at
        self.doctorate.save(update_fields=['admission', 'admission_type', 'admission_approved_by_cdd_at'])

        response = self.client.post(
            self.url,
            {
                'type': ChoixTypeFinancement.WORK_CONTRACT.name,
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(len(form.errors), 2)

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('type_contrat_travail', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('eft', []))

    def test_post_invalid_form_for_a_pre_admission_and_a_scholarship(self):
        self.client.force_login(self.manager.user)

        self.doctorate.admission = self.pre_admission
        self.doctorate.admission_type = self.pre_admission.type
        self.doctorate.admission_approved_by_cdd_at = self.pre_admission.approved_by_cdd_at
        self.doctorate.save(update_fields=['admission', 'admission_type', 'admission_approved_by_cdd_at'])

        response = self.client.post(
            self.url,
            {
                'type': ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(len(form.errors), 2)

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('bourse_recherche', []))
        self.assertIn('', form.errors.get('autre_bourse_recherche', []))

    def test_valid_update_for_self_funding(self):
        self.client.force_login(self.manager.user)

        response = self.client.post(
            self.url,
            {
                **self.default_data,
                'type': ChoixTypeFinancement.SELF_FUNDING.name,
            },
        )
        self.assertEqual(response.status_code, 302)

        self.doctorate.refresh_from_db()

        self.assertEqual(self.doctorate.financing_type, ChoixTypeFinancement.SELF_FUNDING.name)
        self.assertEqual(self.doctorate.other_international_scholarship, '')
        self.assertEqual(self.doctorate.international_scholarship, None)
        self.assertEqual(self.doctorate.financing_work_contract, '')
        self.assertEqual(self.doctorate.financing_eft, None)
        self.assertEqual(self.doctorate.scholarship_start_date, None)
        self.assertEqual(self.doctorate.scholarship_end_date, None)
        self.assertEqual(self.doctorate.scholarship_proof, [])
        self.assertEqual(self.doctorate.planned_duration, self.default_data['duree_prevue'])
        self.assertEqual(self.doctorate.dedicated_time, self.default_data['temps_consacre'])
        self.assertEqual(self.doctorate.is_fnrs_fria_fresh_csc_linked, self.default_data['est_lie_fnrs_fria_fresh_csc'])
        self.assertEqual(self.doctorate.financing_comment, self.default_data['commentaire'])

    def test_valid_update_for_work_contract(self):
        self.client.force_login(self.manager.user)

        response = self.client.post(
            self.url,
            {
                **self.default_data,
                'type': ChoixTypeFinancement.WORK_CONTRACT.name,
            },
        )
        self.assertEqual(response.status_code, 302)

        self.doctorate.refresh_from_db()

        self.assertEqual(self.doctorate.financing_type, ChoixTypeFinancement.WORK_CONTRACT.name)
        self.assertEqual(self.doctorate.other_international_scholarship, '')
        self.assertEqual(self.doctorate.international_scholarship, None)
        self.assertEqual(self.doctorate.financing_work_contract, self.default_data['type_contrat_travail'])
        self.assertEqual(self.doctorate.financing_eft, self.default_data['eft'])
        self.assertEqual(self.doctorate.scholarship_start_date, None)
        self.assertEqual(self.doctorate.scholarship_end_date, None)
        self.assertEqual(self.doctorate.scholarship_proof, [])
        self.assertEqual(self.doctorate.planned_duration, self.default_data['duree_prevue'])
        self.assertEqual(self.doctorate.dedicated_time, self.default_data['temps_consacre'])
        self.assertEqual(self.doctorate.is_fnrs_fria_fresh_csc_linked, self.default_data['est_lie_fnrs_fria_fresh_csc'])
        self.assertEqual(self.doctorate.financing_comment, self.default_data['commentaire'])

    def test_valid_update_for_search_scholarship(self):
        self.client.force_login(self.manager.user)

        response = self.client.post(
            self.url,
            {
                **self.default_data,
                'type': ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
            },
        )
        self.assertEqual(response.status_code, 302)

        self.doctorate.refresh_from_db()

        self.assertEqual(self.doctorate.financing_type, ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name)
        self.assertEqual(self.doctorate.other_international_scholarship, '')
        self.assertEqual(self.doctorate.international_scholarship, self.other_scholarship)
        self.assertEqual(self.doctorate.financing_work_contract, '')
        self.assertEqual(self.doctorate.financing_eft, None)
        self.assertEqual(self.doctorate.scholarship_start_date, self.default_data['bourse_date_debut'])
        self.assertEqual(self.doctorate.scholarship_end_date, self.default_data['bourse_date_fin'])
        self.assertEqual(self.doctorate.scholarship_proof, self.default_data['bourse_preuve_0'])
        self.assertEqual(self.doctorate.planned_duration, self.default_data['duree_prevue'])
        self.assertEqual(self.doctorate.dedicated_time, self.default_data['temps_consacre'])
        self.assertEqual(self.doctorate.is_fnrs_fria_fresh_csc_linked, self.default_data['est_lie_fnrs_fria_fresh_csc'])
        self.assertEqual(self.doctorate.financing_comment, self.default_data['commentaire'])

        response = self.client.post(
            self.url,
            {
                **self.default_data,
                'type': ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
                'bourse_recherche': '',
            },
        )
        self.assertEqual(response.status_code, 302)

        self.doctorate.refresh_from_db()

        self.assertEqual(self.doctorate.financing_type, ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name)
        self.assertEqual(self.doctorate.other_international_scholarship, self.default_data['autre_bourse_recherche'])
        self.assertEqual(self.doctorate.international_scholarship, None)
        self.assertEqual(self.doctorate.financing_work_contract, '')
        self.assertEqual(self.doctorate.financing_eft, None)
        self.assertEqual(self.doctorate.scholarship_start_date, self.default_data['bourse_date_debut'])
        self.assertEqual(self.doctorate.scholarship_end_date, self.default_data['bourse_date_fin'])
        self.assertEqual(self.doctorate.scholarship_proof, self.default_data['bourse_preuve_0'])
        self.assertEqual(self.doctorate.planned_duration, self.default_data['duree_prevue'])
        self.assertEqual(self.doctorate.dedicated_time, self.default_data['temps_consacre'])
        self.assertEqual(self.doctorate.is_fnrs_fria_fresh_csc_linked, self.default_data['est_lie_fnrs_fria_fresh_csc'])
        self.assertEqual(self.doctorate.financing_comment, self.default_data['commentaire'])
