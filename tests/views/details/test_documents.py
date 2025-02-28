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
from typing import List
from unittest.mock import patch
from uuid import uuid4

import freezegun
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext
from rest_framework import status

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from parcours_doctoral.ddd.domain.model.document import TypeDocument
from parcours_doctoral.ddd.domain.model.enums import ChoixEtapeParcoursDoctoral
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ENTITY_CDE, ENTITY_CDSS
from parcours_doctoral.ddd.dtos.document import DocumentDTO
from parcours_doctoral.tests.factories.confirmation_paper import (
    ConfirmationPaperFactory,
)
from parcours_doctoral.tests.factories.document import DocumentFactory
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class DocumentsDetailViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        # First entity
        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)

        # Create doctorates
        cls.doctorate = ParcoursDoctoralFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
        )

        # Create users
        cls.manager = ProgramManagerFactory(education_group=cls.doctorate.training.education_group).person
        cls.other_manager = ProgramManagerFactory().person

        # Create url
        cls.base_url = 'parcours_doctoral:documents'
        cls.url = reverse(cls.base_url, args=[str(cls.doctorate.uuid)])

        cls.confirmation_label = ChoixEtapeParcoursDoctoral.CONFIRMATION.value
        cls.jury_label = ChoixEtapeParcoursDoctoral.JURY.value
        cls.free_label = TypeDocument.LIBRE.value
        cls.system_label = TypeDocument.SYSTEME.value

        cls.confirmation_files_names = [
            'research_report',
            'supervisor_panel_report',
            'supervisor_panel_report_canvas',
            'research_mandate_renewal_opinion',
            'certificate_of_failure',
            'certificate_of_achievement',
            'justification_letter',
        ]

        cls.jury_files_names = [
            'jury_approval',
        ]

        cls.files_names = [
            *cls.confirmation_files_names,
            *cls.jury_files_names,
        ]

        cls.file_uuids = {file_name: str(uuid4()) for file_name in cls.files_names}

        cls.tokens = {file_name: cls.file_uuids[file_name] for file_name in cls.files_names}

        cls.default_upload_date = datetime.datetime(2022, 1, 1)

        cls.default_metadata = {
            'name': 'myfile',
            'mimetype': 'application/pdf',
            'size': 1,
            'uploaded_at': cls.default_upload_date.isoformat(),
            'author': cls.other_manager.global_id,
        }

    def setUp(self):
        # Mock documents
        patcher = patch('osis_document.api.utils.get_remote_tokens')
        patched = patcher.start()
        patched.side_effect = lambda uuids, **kwargs: {value: value for value in uuids}
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document.api.utils.get_several_remote_metadata')
        patched = patcher.start()
        patched.side_effect = lambda tokens: {token: self.default_metadata for token in tokens}
        self.addCleanup(patcher.stop)

        patcher = patch("osis_document.api.utils.get_remote_token", side_effect=lambda value, **kwargs: value)
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("osis_document.api.utils.get_remote_metadata", return_value=self.default_metadata)
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

    def test_with_other_manager(self):
        self.client.force_login(user=self.other_manager.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_with_no_document(self):
        self.client.force_login(user=self.manager.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        documents = response.context['documents_by_section']

        self.assertNotIn(self.confirmation_label, documents)
        self.assertNotIn(self.jury_label, documents)
        self.assertEqual(documents.get(self.free_label), [])
        self.assertEqual(documents.get(self.system_label), [])

        create_form = response.context.get('create_form')
        self.assertIsNotNone(create_form)

    def test_with_confirmation_documents(self):
        self.client.force_login(user=self.manager.user)

        # Add a confirmation paper but without any document
        with freezegun.freeze_time('2022-01-01'):
            confirmation_paper_1 = ConfirmationPaperFactory(
                parcours_doctoral=self.doctorate,
            )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        documents = response.context['documents_by_section']

        self.assertNotIn(self.confirmation_label, documents)

        # Complete with documents
        confirmation_paper_1.research_report = [self.file_uuids['research_report']]
        confirmation_paper_1.supervisor_panel_report = [self.file_uuids['supervisor_panel_report']]
        confirmation_paper_1.supervisor_panel_report_canvas = [self.file_uuids['supervisor_panel_report_canvas']]
        confirmation_paper_1.research_mandate_renewal_opinion = [self.file_uuids['research_mandate_renewal_opinion']]
        confirmation_paper_1.certificate_of_failure = [self.file_uuids['certificate_of_failure']]
        confirmation_paper_1.certificate_of_achievement = [self.file_uuids['certificate_of_achievement']]
        confirmation_paper_1.justification_letter = [self.file_uuids['justification_letter']]

        confirmation_paper_1.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        documents = response.context['documents_by_section']

        self.assertIn(self.confirmation_label, documents)

        confirmation_documents: List[DocumentDTO] = documents.get(self.confirmation_label)
        self.assertEqual(len(confirmation_documents), 7)

        confirmation_labels = {
            'research_report': gettext('Research report'),
            'supervisor_panel_report': gettext('Support Committee minutes'),
            'supervisor_panel_report_canvas': gettext('Canvas of the report of the supervisory panel'),
            'research_mandate_renewal_opinion': gettext('Opinion on research mandate renewal'),
            'certificate_of_failure': gettext('Certificate of failure'),
            'certificate_of_achievement': gettext('Certificate of achievement'),
            'justification_letter': gettext('Justification letter'),
        }
        for index, confirmation_file_name in enumerate(self.confirmation_files_names):
            self.assertEqual(confirmation_documents[index].identifiant, self.file_uuids[confirmation_file_name])
            self.assertEqual(confirmation_documents[index].uuids_documents, [self.file_uuids[confirmation_file_name]])
            self.assertEqual(confirmation_documents[index].type, TypeDocument.NON_LIBRE.name)
            self.assertEqual(confirmation_documents[index].libelle, confirmation_labels[confirmation_file_name])
            self.assertIsNotNone(confirmation_documents[index].auteur)
            self.assertEqual(confirmation_documents[index].auteur.prenom, self.other_manager.first_name)
            self.assertEqual(confirmation_documents[index].auteur.nom, self.other_manager.last_name)
            self.assertEqual(confirmation_documents[index].auteur.matricule, self.other_manager.global_id)

            self.assertEqual(confirmation_documents[index].modifie_le, self.default_upload_date)

        # Add another confirmation paper
        with freezegun.freeze_time('2021-01-01'):
            confirmation_paper_0 = ConfirmationPaperFactory(
                is_active=False,
                parcours_doctoral=self.doctorate,
                research_report=[uuid.uuid4()],
            )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        documents = response.context['documents_by_section']

        first_confirmation_label = ChoixEtapeParcoursDoctoral.CONFIRMATION.value + ' - 1'
        second_confirmation_label = ChoixEtapeParcoursDoctoral.CONFIRMATION.value + ' - 2'

        self.assertNotIn(self.confirmation_label, documents)
        self.assertIsNotNone(documents.get(first_confirmation_label), None)
        self.assertIsNotNone(documents.get(second_confirmation_label), None)

        first_confirmation_documents = documents[first_confirmation_label]
        second_confirmation_documents = documents[second_confirmation_label]

        self.assertEqual(len(first_confirmation_documents), 1)
        self.assertEqual(first_confirmation_documents[0].identifiant, str(confirmation_paper_0.research_report[0]))

        self.assertEqual(len(second_confirmation_documents), 7)

    def test_with_jury_documents(self):
        self.client.force_login(self.manager.user)

        other_doctorate = ParcoursDoctoralFactory(
            training=self.doctorate.training,
            jury_approval=[self.file_uuids['jury_approval']],
        )

        url = reverse(self.base_url, args=[str(other_doctorate.uuid)])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        documents = response.context['documents_by_section']

        self.assertIn(self.jury_label, documents)

        jury_documents = documents[self.jury_label]

        self.assertEqual(len(jury_documents), 1)

        jury_labels = {
            'jury_approval': gettext('Jury approval'),
        }

        for index, jury_file_name in enumerate(self.jury_files_names):
            self.assertEqual(jury_documents[index].identifiant, self.file_uuids[jury_file_name])
            self.assertEqual(jury_documents[index].uuids_documents, [self.file_uuids[jury_file_name]])
            self.assertEqual(jury_documents[index].type, TypeDocument.NON_LIBRE.name)
            self.assertEqual(jury_documents[index].libelle, jury_labels[jury_file_name])
            self.assertIsNotNone(jury_documents[index].auteur)
            self.assertEqual(jury_documents[index].auteur.prenom, self.other_manager.first_name)
            self.assertEqual(jury_documents[index].auteur.nom, self.other_manager.last_name)
            self.assertEqual(jury_documents[index].auteur.matricule, self.other_manager.global_id)
            self.assertEqual(jury_documents[index].modifie_le, self.default_upload_date)

    def test_with_free_documents(self):
        self.client.force_login(self.manager.user)

        with freezegun.freeze_time('2022-01-01'):
            document_1 = DocumentFactory(
                name='Document 1',
                document_type=TypeDocument.LIBRE.name,
                related_doctorate=self.doctorate,
                updated_by=self.manager,
            )

        with freezegun.freeze_time('2021-01-01'):
            document_0 = DocumentFactory(
                name='Document 0',
                document_type=TypeDocument.LIBRE.name,
                related_doctorate=self.doctorate,
                updated_by=self.manager,
            )

        other_document = DocumentFactory(
            name='Other document',
            document_type=TypeDocument.LIBRE.name,
            related_doctorate=ParcoursDoctoralFactory(),
        )

        response = self.client.get(self.url)

        documents = response.context['documents_by_section']

        self.assertIn(self.free_label, documents)

        free_documents = documents[self.free_label]

        self.assertEqual(len(free_documents), 2)

        self.assertEqual(free_documents[0].identifiant, str(document_0.uuid))
        self.assertEqual(free_documents[0].uuids_documents, document_0.file)
        self.assertEqual(free_documents[0].type, TypeDocument.LIBRE.name)
        self.assertEqual(free_documents[0].libelle, document_0.name)
        self.assertIsNotNone(free_documents[0].auteur)
        self.assertEqual(free_documents[0].auteur.prenom, document_0.updated_by.first_name)
        self.assertEqual(free_documents[0].auteur.nom, document_0.updated_by.last_name)
        self.assertEqual(free_documents[0].auteur.matricule, document_0.updated_by.global_id)
        self.assertEqual(free_documents[0].modifie_le, document_0.updated_at)

        self.assertEqual(free_documents[1].identifiant, str(document_1.uuid))
        self.assertEqual(free_documents[1].uuids_documents, document_1.file)
        self.assertEqual(free_documents[1].type, TypeDocument.LIBRE.name)
        self.assertEqual(free_documents[1].libelle, document_1.name)
        self.assertIsNotNone(free_documents[1].auteur)
        self.assertEqual(free_documents[1].auteur.prenom, document_1.updated_by.first_name)
        self.assertEqual(free_documents[1].auteur.nom, document_1.updated_by.last_name)
        self.assertEqual(free_documents[1].auteur.matricule, document_1.updated_by.global_id)
        self.assertEqual(free_documents[1].modifie_le, document_1.updated_at)
