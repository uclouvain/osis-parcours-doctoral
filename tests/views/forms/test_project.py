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
from base.forms.utils import EMPTY_CHOICE, FIELD_REQUIRED_MESSAGE
from base.models.enums.entity_type import EntityType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from parcours_doctoral.ddd.domain.model.enums import (
    ChoixDoctoratDejaRealise,
    ChoixTypeFinancement,
)
from parcours_doctoral.models import ParcoursDoctoral
from parcours_doctoral.tests.factories.parcours_doctoral import (
    FormationFactory,
    ParcoursDoctoralFactory,
)
from reference.tests.factories.language import LanguageFactory
from reference.tests.factories.scholarship import DoctorateScholarshipFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class ProjectFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.institute = EntityVersionFactory(entity_type=EntityType.INSTITUTE.name)
        cls.other_institute = EntityVersionFactory(entity_type=EntityType.INSTITUTE.name)

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

        cls.language = LanguageFactory()
        cls.other_language = LanguageFactory()

    def setUp(self):
        # Mock documents
        patcher = patch("osis_document.api.utils.get_remote_token", side_effect=lambda value, **kwargs: value)
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.get_remote_metadata",
            return_value={"name": "myfile", "mimetype": "application/pdf", "size": 1},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.confirm_remote_upload",
            side_effect=lambda token, *args, **kwargs: token,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch(
            "osis_document.contrib.fields.FileField._confirm_multiple_upload",
            side_effect=lambda _, value, __: value,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        self.doctorate: ParcoursDoctoral = ParcoursDoctoralFactory(
            training=self.training,
            student=self.admission.candidate,
            project_title='Title A',
            project_abstract='Abstract A',
            thesis_language=self.language,
            thesis_institute=self.institute,
            thesis_location='Location A',
            phd_alread_started=True,
            phd_alread_started_institute='Institute A',
            work_start_date=datetime.date(2023, 1, 1),
            phd_already_done=ChoixDoctoratDejaRealise.YES.name,
            phd_already_done_institution='Institute B',
            phd_already_done_thesis_domain='Thesis domain',
            phd_already_done_defense_date=datetime.date(2023, 1, 2),
            phd_already_done_no_defense_reason='No defense reason',
        )

        self.url = reverse('parcours_doctoral:update:project', kwargs={'uuid': self.doctorate.uuid})

        self.default_data = {
            'lieu_these': 'Location B',
            'titre': 'Title B',
            'resume': 'Abstract B',
            'documents_projet_0': [uuid.uuid4()],
            'graphe_gantt_0': [uuid.uuid4()],
            'proposition_programme_doctoral_0': [uuid.uuid4()],
            'projet_formation_complementaire_0': [uuid.uuid4()],
            'lettres_recommandation_0': [uuid.uuid4()],
            'langue_redaction_these': self.other_language.code,
            'institut_these': self.other_institute.uuid,
            'projet_doctoral_deja_commence': True,
            'projet_doctoral_institution': 'Institute C',
            'projet_doctoral_date_debut': datetime.date(2024, 1, 1),
            'doctorat_deja_realise': ChoixDoctoratDejaRealise.YES.name,
            'institution': 'Institute D',
            'domaine_these': 'Thesis domain B',
            'non_soutenue': False,
            'date_soutenance': datetime.date(2025, 1, 1),
            'raison_non_soutenue': 'My new reason',
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

        self.assertEqual(form['lieu_these'].value(), self.doctorate.thesis_location)
        self.assertEqual(form['titre'].value(), self.doctorate.project_title)
        self.assertEqual(form['resume'].value(), self.doctorate.project_abstract)
        self.assertEqual(form['documents_projet'].value(), self.doctorate.project_document)
        self.assertEqual(form['graphe_gantt'].value(), self.doctorate.gantt_graph)
        self.assertEqual(form['proposition_programme_doctoral'].value(), self.doctorate.program_proposition)
        self.assertEqual(form['projet_formation_complementaire'].value(), self.doctorate.additional_training_project)
        self.assertEqual(form['lettres_recommandation'].value(), self.doctorate.recommendation_letters)
        self.assertEqual(form['langue_redaction_these'].value(), self.doctorate.thesis_language.code)
        self.assertEqual(form['institut_these'].value(), self.doctorate.thesis_institute.uuid)
        self.assertEqual(form['projet_doctoral_deja_commence'].value(), self.doctorate.phd_alread_started)
        self.assertEqual(form['projet_doctoral_institution'].value(), self.doctorate.phd_alread_started_institute)
        self.assertEqual(form['projet_doctoral_date_debut'].value(), self.doctorate.work_start_date)
        self.assertEqual(form['doctorat_deja_realise'].value(), self.doctorate.phd_already_done)
        self.assertEqual(form['institution'].value(), self.doctorate.phd_already_done_institution)
        self.assertEqual(form['domaine_these'].value(), self.doctorate.phd_already_done_thesis_domain)
        self.assertEqual(form['non_soutenue'].value(), True)
        self.assertEqual(form['date_soutenance'].value(), self.doctorate.phd_already_done_defense_date)
        self.assertEqual(form['raison_non_soutenue'].value(), self.doctorate.phd_already_done_no_defense_reason)

        for field in [
            'titre',
            'resume',
            'documents_projet',
            'proposition_programme_doctoral',
            'langue_redaction_these',
            'projet_doctoral_deja_commence',
            'projet_doctoral_institution',
            'projet_doctoral_date_debut',
            'institution',
            'domaine_these',
            'raison_non_soutenue',
        ]:
            self.assertEqual(form.label_classes.get(field), 'required_text', field)

        for field in [
            'lieu_these',
            'graphe_gantt',
            'projet_formation_complementaire',
            'lettres_recommandation',
            'institut_these',
            'doctorat_deja_realise',
            'non_soutenue',
            'date_soutenance',
        ]:
            self.assertEqual(form.label_classes.get(field), None, field)

        self.assertCountEqual(
            form.fields['lieu_these'].widget.choices,
            [
                EMPTY_CHOICE[0],
                ('Location A', 'Location A'),
            ],
        )

        self.assertCountEqual(
            form.fields['institut_these'].widget.choices,
            ((self.institute.uuid, f'{self.institute.title} ({self.institute.acronym})'),),
        )

        self.assertCountEqual(
            form.fields['langue_redaction_these'].widget.choices,
            [EMPTY_CHOICE[0], (self.language.code, self.language.name)],
        )

    def test_form_initialization_for_a_pre_admission(self):
        self.client.force_login(user=self.manager.user)

        self.doctorate.admission = self.pre_admission
        self.doctorate.save(update_fields=['admission'])

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context['form']

        for field in [
            'titre',
            'raison_non_soutenue',
        ]:
            self.assertEqual(form.label_classes.get(field), 'required_text', field)

        for field in [
            'resume',
            'documents_projet',
            'proposition_programme_doctoral',
            'langue_redaction_these',
            'projet_doctoral_deja_commence',
            'projet_doctoral_institution',
            'projet_doctoral_date_debut',
            'institution',
            'domaine_these',
            'lieu_these',
            'graphe_gantt',
            'projet_formation_complementaire',
            'lettres_recommandation',
            'institut_these',
            'doctorat_deja_realise',
            'non_soutenue',
            'date_soutenance',
        ]:
            self.assertEqual(form.label_classes.get(field), None, field)

    def test_post_valid_form_without_data(self):
        self.client.force_login(self.manager.user)

        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, 302)

        self.doctorate.refresh_from_db()

        self.assertEqual(self.doctorate.thesis_location, '')
        self.assertEqual(self.doctorate.project_title, '')
        self.assertEqual(self.doctorate.project_abstract, '')
        self.assertEqual(self.doctorate.project_document, [])
        self.assertEqual(self.doctorate.gantt_graph, [])
        self.assertEqual(self.doctorate.program_proposition, [])
        self.assertEqual(self.doctorate.additional_training_project, [])
        self.assertEqual(self.doctorate.recommendation_letters, [])
        self.assertEqual(self.doctorate.thesis_language, None)
        self.assertEqual(self.doctorate.thesis_institute, None)
        self.assertEqual(self.doctorate.phd_alread_started, None)
        self.assertEqual(self.doctorate.phd_alread_started_institute, '')
        self.assertEqual(self.doctorate.work_start_date, None)
        self.assertEqual(self.doctorate.phd_already_done, ChoixDoctoratDejaRealise.NO.name)
        self.assertEqual(self.doctorate.phd_already_done_institution, '')
        self.assertEqual(self.doctorate.phd_already_done_thesis_domain, '')
        self.assertEqual(self.doctorate.phd_already_done_defense_date, None)
        self.assertEqual(self.doctorate.phd_already_done_no_defense_reason, '')

    def test_post_invalid_form_if_phd_already_done_with_missing_data(self):
        self.client.force_login(self.manager.user)

        response = self.client.post(
            self.url,
            {
                'doctorat_deja_realise': ChoixDoctoratDejaRealise.YES.name,
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(len(form.errors), 2)

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('domaine_these', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('institution', []))

        response = self.client.post(
            self.url,
            {
                'doctorat_deja_realise': ChoixDoctoratDejaRealise.YES.name,
                'non_soutenue': 'True',
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(len(form.errors), 3)

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('domaine_these', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('institution', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('raison_non_soutenue', []))

    def test_post_valid_form(self):
        self.client.force_login(self.manager.user)

        response = self.client.post(
            self.url,
            self.default_data,
        )

        self.assertEqual(response.status_code, 302)

        self.doctorate.refresh_from_db()

        self.assertEqual(self.doctorate.thesis_location, self.default_data['lieu_these'])
        self.assertEqual(self.doctorate.project_title, self.default_data['titre'])
        self.assertEqual(self.doctorate.project_abstract, self.default_data['resume'])
        self.assertEqual(self.doctorate.project_document, self.default_data['documents_projet_0'])
        self.assertEqual(self.doctorate.gantt_graph, self.default_data['graphe_gantt_0'])
        self.assertEqual(self.doctorate.program_proposition, self.default_data['proposition_programme_doctoral_0'])
        self.assertEqual(
            self.doctorate.additional_training_project, self.default_data['projet_formation_complementaire_0']
        )
        self.assertEqual(self.doctorate.recommendation_letters, self.default_data['lettres_recommandation_0'])
        self.assertEqual(self.doctorate.thesis_language.code, self.default_data['langue_redaction_these'])
        self.assertEqual(self.doctorate.thesis_institute.uuid, self.default_data['institut_these'])
        self.assertEqual(self.doctorate.phd_alread_started, self.default_data['projet_doctoral_deja_commence'])
        self.assertEqual(self.doctorate.phd_alread_started_institute, self.default_data['projet_doctoral_institution'])
        self.assertEqual(self.doctorate.work_start_date, self.default_data['projet_doctoral_date_debut'])
        self.assertEqual(self.doctorate.phd_already_done, self.default_data['doctorat_deja_realise'])
        self.assertEqual(self.doctorate.phd_already_done_institution, self.default_data['institution'])
        self.assertEqual(self.doctorate.phd_already_done_thesis_domain, self.default_data['domaine_these'])
        self.assertEqual(self.doctorate.phd_already_done_defense_date, self.default_data['date_soutenance'])
        self.assertEqual(self.doctorate.phd_already_done_no_defense_reason, '')

        response = self.client.post(
            self.url,
            {
                **self.default_data,
                'non_soutenue': 'True',
            },
        )

        self.assertEqual(response.status_code, 302)

        self.doctorate.refresh_from_db()

        self.assertEqual(self.doctorate.phd_already_done_defense_date, None)
        self.assertEqual(self.doctorate.phd_already_done_no_defense_reason, self.default_data['raison_non_soutenue'])

        response = self.client.post(
            self.url,
            {
                **self.default_data,
                'doctorat_deja_realise': ChoixDoctoratDejaRealise.NO.name,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.doctorate.refresh_from_db()

        self.assertEqual(self.doctorate.phd_already_done, ChoixDoctoratDejaRealise.NO.name)
        self.assertEqual(self.doctorate.phd_already_done_institution, '')
        self.assertEqual(self.doctorate.phd_already_done_thesis_domain, '')
        self.assertEqual(self.doctorate.phd_already_done_defense_date, None)
        self.assertEqual(self.doctorate.phd_already_done_no_defense_reason, '')
