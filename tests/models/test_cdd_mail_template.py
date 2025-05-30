# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from base.models.enums.entity_type import EntityType
from base.tests.factories.entity_version import (
    EntityVersionFactory,
    MainEntityVersionFactory,
)
from django.conf import settings
from django.test import TransactionTestCase

from parcours_doctoral.mail_templates import (
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT,
)
from parcours_doctoral.models.cdd_mail_template import CddMailTemplate
from parcours_doctoral.tests.factories.mail_template import CddMailTemplateFactory


class CDDMailTemplateTestCase(TransactionTestCase):
    @classmethod
    def setUpClass(cls):
        cls.main_entity = MainEntityVersionFactory().entity

        cls.fac_1_entity = EntityVersionFactory(
            parent=cls.main_entity,
            entity_type=EntityType.FACULTY.name,
        ).entity

        cls.fac_2_entity = EntityVersionFactory(
            parent=cls.main_entity,
            entity_type=EntityType.FACULTY.name,
        ).entity

        cls.fac_1_school_1_entity = EntityVersionFactory(
            parent=cls.fac_1_entity,
            entity_type=EntityType.SCHOOL.name,
        ).entity

        cls.fac_1_school_1_cdd_1_entity = EntityVersionFactory(
            parent=cls.fac_1_school_1_entity,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
        ).entity

    def test_get_from_identifiers(self):
        first_cdd_mail_template = CddMailTemplateFactory(
            subject='Subject',
            body='Body',
            name='Some name',
            identifier=PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT,
            language=settings.LANGUAGE_CODE_FR,
            cdd=self.fac_1_school_1_cdd_1_entity,
        )

        # The template is linked to the CDD entity
        retrieved_cdd_mail_templates = CddMailTemplate.objects.get_from_identifiers(
            identifiers=[first_cdd_mail_template.identifier],
            language=first_cdd_mail_template.language,
            cdd_id=self.fac_1_school_1_cdd_1_entity.id,
        )

        self.assertEqual(len(retrieved_cdd_mail_templates), 1)
        self.assertEqual(retrieved_cdd_mail_templates[0], first_cdd_mail_template)

        # The template is linked to the school entity
        first_cdd_mail_template.cdd = self.fac_1_school_1_entity
        first_cdd_mail_template.save()

        retrieved_cdd_mail_templates = CddMailTemplate.objects.get_from_identifiers(
            identifiers=[first_cdd_mail_template.identifier],
            language=first_cdd_mail_template.language,
            cdd_id=self.fac_1_school_1_entity.id,
        )

        self.assertEqual(len(retrieved_cdd_mail_templates), 1)
        self.assertEqual(retrieved_cdd_mail_templates[0], first_cdd_mail_template)

        # The template is linked to the faculty entity
        first_cdd_mail_template.cdd = self.fac_1_entity
        first_cdd_mail_template.save()

        retrieved_cdd_mail_templates = CddMailTemplate.objects.get_from_identifiers(
            identifiers=[first_cdd_mail_template.identifier],
            language=first_cdd_mail_template.language,
            cdd_id=self.fac_1_entity.id,
        )

        self.assertEqual(len(retrieved_cdd_mail_templates), 1)
        self.assertEqual(retrieved_cdd_mail_templates[0], first_cdd_mail_template)

        # Other identifier
        retrieved_cdd_mail_templates = CddMailTemplate.objects.get_from_identifiers(
            identifiers=['CUSTOM_IDENTIFIER'],
            language=first_cdd_mail_template.language,
            cdd_id=self.fac_1_school_1_cdd_1_entity.id,
        )

        self.assertEqual(len(retrieved_cdd_mail_templates), 0)

        # Other language
        retrieved_cdd_mail_templates = CddMailTemplate.objects.get_from_identifiers(
            identifiers=[first_cdd_mail_template.identifier],
            language=settings.LANGUAGE_CODE_EN,
            cdd_id=self.fac_1_school_1_cdd_1_entity.id,
        )

        self.assertEqual(len(retrieved_cdd_mail_templates), 0)

        # Other entity
        retrieved_cdd_mail_templates = CddMailTemplate.objects.get_from_identifiers(
            identifiers=[first_cdd_mail_template.identifier],
            language=first_cdd_mail_template.language,
            cdd_id=self.fac_2_entity.id,
        )

        self.assertEqual(len(retrieved_cdd_mail_templates), 0)
