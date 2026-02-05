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
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ENTITY_CDE
from parcours_doctoral.ddd.dtos.document import DocumentDTO
from parcours_doctoral.tests.factories.admissibility import AdmissibilityFactory
from parcours_doctoral.tests.factories.confirmation_paper import (
    ConfirmationPaperFactory,
)
from parcours_doctoral.tests.factories.document import DocumentFactory
from parcours_doctoral.tests.factories.parcours_doctoral import FormationFactory, ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.private_defense import PrivateDefenseFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class DocumentsDetailViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        # First entity
        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)

        # Create training
        cls.training = FormationFactory(
            management_entity=first_doctoral_commission,
            academic_year=academic_years[0],
        )

        # Create users
        cls.manager = ProgramManagerFactory(education_group=cls.training.education_group).person
        cls.other_manager = ProgramManagerFactory().person

        # Create url
        cls.base_url = 'parcours_doctoral:documents'

        cls.free_label = TypeDocument.LIBRE.value
        cls.system_label = TypeDocument.SYSTEME.value

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
        patcher = patch('osis_document_components.services.get_remote_tokens')
        patched = patcher.start()
        patched.side_effect = lambda uuids, **kwargs: {value: value for value in uuids}
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document_components.services.get_several_remote_metadata')
        patched = patcher.start()
        patched.side_effect = lambda tokens: {token: self.default_metadata for token in tokens}
        self.addCleanup(patcher.stop)

        patcher = patch("osis_document_components.services.get_remote_token", side_effect=lambda value, **kwargs: value)
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("osis_document_components.services.get_remote_metadata", return_value=self.default_metadata)
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

        self.doctorate = ParcoursDoctoralFactory(training=self.training)
        self.url = reverse(self.base_url, args=[str(self.doctorate.uuid)])

    def test_with_other_manager(self):
        self.client.force_login(user=self.other_manager.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_with_no_document(self):
        self.client.force_login(user=self.manager.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        documents = response.context['documents_by_section']

        self.assertEqual(documents.get(self.free_label), [])
        self.assertEqual(documents.get(self.system_label), [])
        self.assertEqual(len(documents), 2)

        create_form = response.context.get('create_form')
        self.assertIsNotNone(create_form)

    def test_with_confirmation_documents(self):
        self.client.force_login(user=self.manager.user)

        category_label = ChoixEtapeParcoursDoctoral.CONFIRMATION.value

        file_uuids = {
            file_name: str(uuid.uuid4())
            for file_name in [
                'research_report',
                'supervisor_panel_report',
                'supervisor_panel_report_canvas',
                'research_mandate_renewal_opinion',
                'certificate_of_failure',
                'certificate_of_achievement',
                'justification_letter',
            ]
        }

        # Add a confirmation paper but without any document
        with freezegun.freeze_time('2022-01-01'):
            confirmation_paper_1 = ConfirmationPaperFactory(
                parcours_doctoral=self.doctorate,
            )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        documents = response.context['documents_by_section']

        self.assertNotIn(category_label, documents)

        # Complete with documents
        confirmation_paper_1.research_report = [file_uuids['research_report']]
        confirmation_paper_1.supervisor_panel_report = [file_uuids['supervisor_panel_report']]
        confirmation_paper_1.supervisor_panel_report_canvas = [file_uuids['supervisor_panel_report_canvas']]
        confirmation_paper_1.research_mandate_renewal_opinion = [file_uuids['research_mandate_renewal_opinion']]
        confirmation_paper_1.certificate_of_failure = [file_uuids['certificate_of_failure']]
        confirmation_paper_1.certificate_of_achievement = [file_uuids['certificate_of_achievement']]
        confirmation_paper_1.justification_letter = [file_uuids['justification_letter']]

        confirmation_paper_1.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        documents = response.context['documents_by_section']

        self.assertIn(category_label, documents)

        category_documents: List[DocumentDTO] = documents[category_label]
        self.assertEqual(len(category_documents), 7)

        labels = {
            'research_report': gettext('Research report'),
            'supervisor_panel_report': gettext('Support Committee minutes'),
            'supervisor_panel_report_canvas': gettext('Canvas of the report of the supervisory panel'),
            'research_mandate_renewal_opinion': gettext('Opinion on research mandate renewal'),
            'certificate_of_failure': gettext('Certificate of failure'),
            'certificate_of_achievement': gettext('Certificate of achievement'),
            'justification_letter': gettext('Justification letter'),
        }
        for index, (file_name, file_uuid) in enumerate(file_uuids.items()):
            self.assertEqual(category_documents[index].identifiant, file_uuid)
            self.assertEqual(category_documents[index].uuids_documents, [file_uuid])
            self.assertEqual(category_documents[index].type, TypeDocument.NON_LIBRE.name)
            self.assertEqual(category_documents[index].libelle, labels[file_name])
            self.assertIsNotNone(category_documents[index].auteur)
            self.assertEqual(category_documents[index].auteur.prenom, self.other_manager.first_name)
            self.assertEqual(category_documents[index].auteur.nom, self.other_manager.last_name)
            self.assertEqual(category_documents[index].auteur.matricule, self.other_manager.global_id)

            self.assertEqual(category_documents[index].modifie_le, self.default_upload_date)

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
        first_confirmation_label = ChoixEtapeParcoursDoctoral.CONFIRMATION.value + ' ' + gettext('no.') + '1'
        second_confirmation_label = ChoixEtapeParcoursDoctoral.CONFIRMATION.value + ' ' + gettext('no.') + '2'

        self.assertNotIn(category_label, documents)
        self.assertIsNotNone(documents.get(first_confirmation_label), None)
        self.assertIsNotNone(documents.get(second_confirmation_label), None)

        first_confirmation_documents = documents[first_confirmation_label]
        second_confirmation_documents = documents[second_confirmation_label]

        self.assertEqual(len(first_confirmation_documents), 1)
        self.assertEqual(first_confirmation_documents[0].identifiant, str(confirmation_paper_0.research_report[0]))

        self.assertEqual(len(second_confirmation_documents), 7)

    def test_with_jury_documents(self):
        self.client.force_login(self.manager.user)

        category_label = ChoixEtapeParcoursDoctoral.JURY.value

        file_uuids = {
            file_name: str(uuid.uuid4())
            for file_name in [
                'jury_approval',
            ]
        }

        self.doctorate.jury_approval = [file_uuids['jury_approval']]
        self.doctorate.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        documents = response.context['documents_by_section']

        self.assertIn(category_label, documents)

        category_documents = documents[category_label]

        self.assertEqual(len(category_documents), 1)

        labels = {
            'jury_approval': gettext('Jury approval'),
        }

        for index, (file_name, file_uuid) in enumerate(file_uuids.items()):
            self.assertEqual(category_documents[index].identifiant, file_uuid)
            self.assertEqual(category_documents[index].uuids_documents, [file_uuid])
            self.assertEqual(category_documents[index].type, TypeDocument.NON_LIBRE.name)
            self.assertEqual(category_documents[index].libelle, labels[file_name])
            self.assertIsNotNone(category_documents[index].auteur)
            self.assertEqual(category_documents[index].auteur.prenom, self.other_manager.first_name)
            self.assertEqual(category_documents[index].auteur.nom, self.other_manager.last_name)
            self.assertEqual(category_documents[index].auteur.matricule, self.other_manager.global_id)
            self.assertEqual(category_documents[index].modifie_le, self.default_upload_date)

    def test_with_admissibility_documents(self):
        self.client.force_login(self.manager.user)

        category_label = ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.value

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        documents = response.context['documents_by_section']
        self.assertNotIn(category_label, documents)

        # Add documents
        file_uuids = {
            file_name: str(uuid.uuid4())
            for file_name in [
                'thesis_exam_board_opinion',
                'minutes',
                'minutes_canvas',
            ]
        }

        AdmissibilityFactory(
            thesis_exam_board_opinion=[file_uuids['thesis_exam_board_opinion']],
            minutes=[file_uuids['minutes']],
            minutes_canvas=[file_uuids['minutes_canvas']],
            parcours_doctoral=self.doctorate,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        documents = response.context['documents_by_section']

        self.assertIn(category_label, documents)

        category_documents = documents[category_label]

        self.assertEqual(len(category_documents), 3)

        labels = {
            'thesis_exam_board_opinion': gettext('Thesis exam board opinion'),
            'minutes': gettext('Admissibility minutes'),
            'minutes_canvas': gettext('Admissibility minutes canvas'),
        }

        for index, (file_name, file_uuid) in enumerate(file_uuids.items()):
            self.assertEqual(category_documents[index].identifiant, file_uuids[file_name])
            self.assertEqual(category_documents[index].uuids_documents, [file_uuids[file_name]])
            self.assertEqual(category_documents[index].type, TypeDocument.NON_LIBRE.name)
            self.assertEqual(category_documents[index].libelle, labels[file_name])
            self.assertIsNotNone(category_documents[index].auteur)
            self.assertEqual(category_documents[index].auteur.prenom, self.other_manager.first_name)
            self.assertEqual(category_documents[index].auteur.nom, self.other_manager.last_name)
            self.assertEqual(category_documents[index].auteur.matricule, self.other_manager.global_id)
            self.assertEqual(category_documents[index].modifie_le, self.default_upload_date)

    def test_with_private_defense_documents(self):
        self.client.force_login(self.manager.user)

        category_label = ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.value

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        documents = response.context['documents_by_section']

        self.assertNotIn(category_label, documents)

        # Add documents
        file_uuids = {
            file_name: str(uuid.uuid4())
            for file_name in [
                'minutes',
                'minutes_canvas',
            ]
        }

        PrivateDefenseFactory(
            minutes=[file_uuids['minutes']],
            minutes_canvas=[file_uuids['minutes_canvas']],
            parcours_doctoral=self.doctorate,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        documents = response.context['documents_by_section']

        self.assertIn(category_label, documents)

        category_documents = documents[category_label]

        self.assertEqual(len(category_documents), 2)

        labels = {
            'minutes': gettext('Private defence minutes'),
            'minutes_canvas': gettext('Private defence minutes canvas'),
        }

        for index, (file_name, file_uuid) in enumerate(file_uuids.items()):
            self.assertEqual(category_documents[index].identifiant, file_uuid)
            self.assertEqual(category_documents[index].uuids_documents, [file_uuid])
            self.assertEqual(category_documents[index].type, TypeDocument.NON_LIBRE.name)
            self.assertEqual(category_documents[index].libelle, labels[file_name])
            self.assertIsNotNone(category_documents[index].auteur)
            self.assertEqual(category_documents[index].auteur.prenom, self.other_manager.first_name)
            self.assertEqual(category_documents[index].auteur.nom, self.other_manager.last_name)
            self.assertEqual(category_documents[index].auteur.matricule, self.other_manager.global_id)
            self.assertEqual(category_documents[index].modifie_le, self.default_upload_date)

    def test_with_public_defense_documents(self):
        self.client.force_login(self.manager.user)

        category_label = ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.value

        # Without document
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        documents = response.context['documents_by_section']

        self.assertNotIn(category_label, documents)

        # With documents
        file_uuids = {
            file_name: str(uuid.uuid4())
            for file_name in [
                'announcement_photo',
                'defense_minutes',
                'defense_minutes_canvas',
            ]
        }
        self.doctorate.announcement_photo = [file_uuids['announcement_photo']]
        self.doctorate.defense_minutes = [file_uuids['defense_minutes']]
        self.doctorate.defense_minutes_canvas = [file_uuids['defense_minutes_canvas']]
        self.doctorate.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        documents = response.context['documents_by_section']

        self.assertIn(category_label, documents)

        category_documents = documents[category_label]

        self.assertEqual(len(category_documents), 3)

        labels = {
            'announcement_photo': gettext('Photo for announcement'),
            'defense_minutes': gettext('Public defence minutes'),
            'defense_minutes_canvas': gettext('Public defence minutes canvas'),
        }

        for index, (file_name, file_uuid) in enumerate(file_uuids.items()):
            self.assertEqual(category_documents[index].identifiant, file_uuid)
            self.assertEqual(category_documents[index].uuids_documents, [file_uuid])
            self.assertEqual(category_documents[index].type, TypeDocument.NON_LIBRE.name)
            self.assertEqual(category_documents[index].libelle, labels[file_name])
            self.assertIsNotNone(category_documents[index].auteur)
            self.assertEqual(category_documents[index].auteur.prenom, self.other_manager.first_name)
            self.assertEqual(category_documents[index].auteur.nom, self.other_manager.last_name)
            self.assertEqual(category_documents[index].auteur.matricule, self.other_manager.global_id)
            self.assertEqual(category_documents[index].modifie_le, self.default_upload_date)

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

        DocumentFactory(
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
