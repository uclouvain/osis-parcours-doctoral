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
from unittest.mock import patch

from django.test import TestCase, override_settings
from osis_document_components.fields import FileUploadField

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from parcours_doctoral.ddd.domain.model.document import TypeDocument
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ENTITY_CDE
from parcours_doctoral.tests.factories.document import DocumentFactory
from parcours_doctoral.tests.factories.parcours_doctoral import (
    ParcoursDoctoralFactory,
    create_valid_enrolment,
)


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class DocumentBaseTestCase(TestCase):
    with_existing_document = False

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
        create_valid_enrolment(doctorate=cls.doctorate, year=2021)

        # Create users
        cls.manager = ProgramManagerFactory(education_group=cls.doctorate.training.education_group).person
        cls.other_manager = ProgramManagerFactory().person

        cls.default_upload_date = datetime.datetime(2022, 1, 1)

        cls.default_metadata = {
            'name': 'myfile',
            'mimetype': 'application/pdf',
            'size': 1,
            'uploaded_at': cls.default_upload_date.isoformat(),
            'author': cls.other_manager.global_id,
        }

        cls.file_missing_message = FileUploadField.default_error_messages['min_files']

    def setUp(self):
        # Mock documents
        patcher = patch('osis_document_components.services.get_remote_tokens')
        patched = patcher.start()
        patched.side_effect = lambda uuids, **kwargs: {value: 'token' for value in uuids}
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document_components.services.get_several_remote_metadata')
        patched = patcher.start()
        patched.side_effect = lambda tokens: {token: self.default_metadata for token in tokens}
        self.addCleanup(patcher.stop)

        patcher = patch("osis_document_components.services.get_remote_token", return_value='token')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("osis_document_components.services.get_remote_metadata", return_value=self.default_metadata)
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("parcours_doctoral.views.document.mixins.get_remote_token", return_value='token')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "parcours_doctoral.views.document.mixins.get_remote_metadata", return_value=self.default_metadata
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

        if self.with_existing_document:
            self.document = DocumentFactory(
                related_doctorate=self.doctorate,
                updated_by=self.other_manager,
                document_type=TypeDocument.LIBRE.name,
                name='My document',
            )
