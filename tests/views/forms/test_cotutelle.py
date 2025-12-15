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
import uuid
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import (
    ENTITY_CDE,
)
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from parcours_doctoral.models import ParcoursDoctoral
from parcours_doctoral.tests.factories.parcours_doctoral import (
    FormationFactory,
    ParcoursDoctoralFactory,
)


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class CotutelleFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)

        cls.organization = EntityVersionFactory().entity.organization
        cls.other_organization = EntityVersionFactory().entity.organization

        cls.training = FormationFactory(
            management_entity=first_doctoral_commission,
            academic_year=academic_years[0],
        )

        cls.manager = ProgramManagerFactory(education_group=cls.training.education_group).person

        cls.other_manager = ProgramManagerFactory().person

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
            cotutelle=True,
            cotutelle_motivation='Motivation',
            cotutelle_institution_fwb=True,
            cotutelle_institution=self.organization.uuid,
            cotutelle_other_institution_name='',
            cotutelle_other_institution_address='',
            cotutelle_opening_request=[uuid.uuid4()],
            cotutelle_convention=[uuid.uuid4()],
            cotutelle_other_documents=[uuid.uuid4()],
        )

        self.url = reverse('parcours_doctoral:update:cotutelle', kwargs={'uuid': self.doctorate.uuid})

        self.default_data = {
            'cotutelle': 'YES',
            'motivation': 'new motivation',
            'demande_ouverture_0': [uuid.uuid4()],
            'convention_0': [uuid.uuid4()],
            'autres_documents_0': [uuid.uuid4()],
            'institution_fwb': 'true',
            'institution': str(self.other_organization.uuid),
            'autre_institution': 'false',
            'autre_institution_nom': 'New name',
            'autre_institution_adresse': 'New address',
        }

    def test_with_other_manager(self):
        self.client.force_login(user=self.other_manager.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_form_initialization(self):
        self.client.force_login(user=self.manager.user)

        # With cotutelle
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertEqual(form['cotutelle'].value(), 'YES')
        self.assertEqual(form['motivation'].value(), self.doctorate.cotutelle_motivation)
        self.assertEqual(form['institution_fwb'].value(), 'true')
        self.assertEqual(form['institution'].value(), str(self.doctorate.cotutelle_institution))
        self.assertEqual(form['autre_institution'].value(), False)
        self.assertEqual(form['autre_institution_nom'].value(), self.doctorate.cotutelle_other_institution_name)
        self.assertEqual(form['autre_institution_adresse'].value(), self.doctorate.cotutelle_other_institution_address)
        self.assertEqual(form['demande_ouverture'].value(), self.doctorate.cotutelle_opening_request)
        self.assertEqual(form['convention'].value(), self.doctorate.cotutelle_convention)
        self.assertEqual(form['autres_documents'].value(), self.doctorate.cotutelle_other_documents)

        # With cotutelle and custom cotutelle institute
        self.doctorate.cotutelle_institution = None
        self.doctorate.cotutelle_other_institution_name = 'Other institution'
        self.doctorate.cotutelle_other_institution_address = 'Other address'
        self.doctorate.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertEqual(form['autre_institution'].value(), True)
        self.assertEqual(form['autre_institution_nom'].value(), self.doctorate.cotutelle_other_institution_name)
        self.assertEqual(form['autre_institution_adresse'].value(), self.doctorate.cotutelle_other_institution_address)

        # Without cotutelle
        self.doctorate.cotutelle = False
        self.doctorate.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertEqual(form['cotutelle'].value(), 'NO')

    def test_submit_invalid_form(self):
        self.client.force_login(user=self.manager.user)

        # With no data
        response = self.client.post(self.url, data={})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertEqual(len(form.errors), 1)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('cotutelle', []))

        # With cotutelle but without additional data
        response = self.client.post(
            self.url,
            data={
                'cotutelle': 'YES',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertEqual(len(form.errors), 3)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('motivation', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('institution', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('institution_fwb', []))

        # With other institute
        response = self.client.post(
            self.url,
            data={
                'cotutelle': 'YES',
                'autre_institution': 'true',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertEqual(len(form.errors), 4)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('motivation', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('autre_institution_nom', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('autre_institution_adresse', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('institution_fwb', []))

    def test_submit_valid_form_with_no_cotutelle(self):
        self.client.force_login(user=self.manager.user)

        self.default_data['cotutelle'] = 'NO'

        response = self.client.post(self.url, data=self.default_data)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.doctorate.refresh_from_db()

        self.assertFalse(self.doctorate.cotutelle)
        self.assertEqual(self.doctorate.cotutelle_motivation, '')
        self.assertEqual(self.doctorate.cotutelle_institution_fwb, None)
        self.assertEqual(self.doctorate.cotutelle_institution, None)
        self.assertEqual(self.doctorate.cotutelle_other_institution_name, '')
        self.assertEqual(self.doctorate.cotutelle_other_institution_address, '')
        self.assertEqual(self.doctorate.cotutelle_opening_request, [])
        self.assertEqual(self.doctorate.cotutelle_convention, [])
        self.assertEqual(self.doctorate.cotutelle_other_documents, [])

    def test_submit_valid_form_with_cotutelle_and_existing_institute(self):
        self.client.force_login(user=self.manager.user)

        response = self.client.post(self.url, data=self.default_data)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.doctorate.refresh_from_db()

        self.assertTrue(self.doctorate.cotutelle)
        self.assertEqual(self.doctorate.cotutelle_motivation, self.default_data['motivation'])
        self.assertTrue(self.doctorate.cotutelle_institution_fwb)
        self.assertEqual(str(self.doctorate.cotutelle_institution), self.default_data['institution'])
        self.assertEqual(self.doctorate.cotutelle_other_institution_name, '')
        self.assertEqual(self.doctorate.cotutelle_other_institution_address, '')
        self.assertEqual(self.doctorate.cotutelle_opening_request, self.default_data['demande_ouverture_0'])
        self.assertEqual(self.doctorate.cotutelle_convention, self.default_data['convention_0'])
        self.assertEqual(self.doctorate.cotutelle_other_documents, self.default_data['autres_documents_0'])

    def test_submit_valid_form_with_cotutelle_and_no_fwb_but_custom_institute(self):
        self.client.force_login(user=self.manager.user)

        self.default_data['autre_institution'] = 'true'
        self.default_data['institution_fwb'] = 'false'

        response = self.client.post(self.url, data=self.default_data)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.doctorate.refresh_from_db()

        self.assertTrue(self.doctorate.cotutelle)
        self.assertEqual(self.doctorate.cotutelle_motivation, self.default_data['motivation'])
        self.assertFalse(self.doctorate.cotutelle_institution_fwb)
        self.assertEqual(self.doctorate.cotutelle_institution, None)
        self.assertEqual(self.doctorate.cotutelle_other_institution_name, self.default_data['autre_institution_nom'])
        self.assertEqual(
            self.doctorate.cotutelle_other_institution_address, self.default_data['autre_institution_adresse']
        )
        self.assertEqual(self.doctorate.cotutelle_opening_request, self.default_data['demande_ouverture_0'])
        self.assertEqual(self.doctorate.cotutelle_convention, self.default_data['convention_0'])
        self.assertEqual(self.doctorate.cotutelle_other_documents, self.default_data['autres_documents_0'])
