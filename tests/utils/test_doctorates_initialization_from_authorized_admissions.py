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
from unittest.mock import patch

from django.test import TestCase, override_settings

from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.models import DoctorateAdmission
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.supervision import PromoterFactory
from base.forms.utils.file_field import PDF_MIME_TYPE
from parcours_doctoral.models import ParcoursDoctoral
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.utils.doctorates_initialization_from_authorized_admissions import (
    initialize_the_doctorates_from_authorized_admissions,
)


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class InitializeTheDoctoratesFromAuthorizedAdmissionsTestCase(TestCase):
    def setUp(self):
        # Mock documents
        patcher = patch('osis_document_components.services.get_remote_tokens')
        patched = patcher.start()
        patched.side_effect = lambda uuids, **kwargs: {uuid: f'token-{index}' for index, uuid in enumerate(uuids)}
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document_components.services.get_several_remote_metadata')
        patched = patcher.start()
        patched.side_effect = lambda tokens: {
            token: {
                'name': 'myfile',
                'mimetype': PDF_MIME_TYPE,
                'size': 1,
            }
            for token in tokens
        }
        self.addCleanup(patcher.stop)

        patcher = patch("osis_document_components.services.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document_components.services.get_remote_metadata",
            return_value={"name": "myfile", "size": 1},
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

        patcher = patch(
            'parcours_doctoral.infrastructure.parcours_doctoral.domain.service.parcours_doctoral.'
            'documents_remote_duplicate'
        )
        patched = patcher.start()
        patched.side_effect = lambda uuids, upload_path_by_uuid: {
            str(current_uuid): str(current_uuid) for current_uuid in uuids
        }
        self.addCleanup(patcher.stop)

    def test_do_not_initialize_the_doctorate_if_the_admission_is_not_authorized(self):
        admission: DoctorateAdmission = DoctorateAdmissionFactory(
            status=ChoixStatutPropositionDoctorale.INSCRIPTION_REFUSEE.name
        )

        valid_references, invalid_references = initialize_the_doctorates_from_authorized_admissions(DoctorateAdmission)

        self.assertEqual(len(valid_references), 0)
        self.assertEqual(len(invalid_references), 0)

        admission.refresh_from_db()

        doctorates = admission.parcoursdoctoral_set.all()

        self.assertEqual(len(doctorates), 0)

    def test_do_not_initialize_the_doctorate_if_it_already_exists(self):
        doctorate: ParcoursDoctoral = ParcoursDoctoralFactory(
            admission__status=ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name,
        )

        valid_references, invalid_references = initialize_the_doctorates_from_authorized_admissions(DoctorateAdmission)

        self.assertEqual(len(valid_references), 0)
        self.assertEqual(len(invalid_references), 0)

        doctorates = doctorate.admission.parcoursdoctoral_set.all()

        self.assertEqual(len(doctorates), 1)

    def test_initialize_the_doctorate_if_the_admission_is_authorized(self):
        admission: DoctorateAdmission = DoctorateAdmissionFactory(
            status=ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name,
            supervision_group=PromoterFactory().process,
        )

        valid_references, invalid_references = initialize_the_doctorates_from_authorized_admissions(DoctorateAdmission)

        self.assertEqual(len(valid_references), 1)
        self.assertEqual(len(invalid_references), 0)

        admission.refresh_from_db()

        doctorates = admission.parcoursdoctoral_set.all()

        self.assertEqual(len(doctorates), 1)
