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
from django.shortcuts import resolve_url
from django.test import TestCase
from rest_framework import status

from base.models.enums.entity_type import EntityType
from base.models.enums.organization_type import MAIN
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.person import PersonFactory, SuperUserPersonFactory
from parcours_doctoral.auth.roles.auditor import Auditor
from parcours_doctoral.tests.factories.roles import (
    AuditorFactory,
    SectorAdministrativeDirectorFactory,
)


class AuditorsTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.das = SectorAdministrativeDirectorFactory()
        cls.entity1 = EntityWithVersionFactory(
            organization__type=MAIN,
            version__entity_type=EntityType.INSTITUTE.name,
        )
        cls.entity2 = EntityWithVersionFactory(
            organization__type=MAIN,
            version__entity_type=EntityType.INSTITUTE.name,
        )
        cls.person1 = PersonFactory()
        cls.person2 = PersonFactory()
        cls.auditor = AuditorFactory(
            entity=cls.entity1,
            person=cls.person1,
        )

    def test_get(self):
        url = resolve_url('parcours_doctoral:config:auditors')
        self.client.force_login(self.das.person.user)
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'parcours_doctoral/config/auditors.html')

    def test_post_create(self):
        url = resolve_url('parcours_doctoral:config:auditors')
        self.client.force_login(self.das.person.user)
        response = self.client.post(
            url,
            data={
                "form-TOTAL_FORMS": "2",
                "form-INITIAL_FORMS": "2",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
                "form-0-auditor": str(self.person1.id),
                "form-1-auditor": str(self.person2.id),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(Auditor.objects.count(), 2)
        self.assertEqual(Auditor.objects.all()[1].person, self.person2)
        self.assertEqual(Auditor.objects.all()[1].entity, self.entity2)

    def test_post_update(self):
        url = resolve_url('parcours_doctoral:config:auditors')
        self.client.force_login(self.das.person.user)
        response = self.client.post(
            url,
            data={
                "form-TOTAL_FORMS": "2",
                "form-INITIAL_FORMS": "2",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
                "form-0-auditor": str(self.person2.id),
                "form-1-auditor": "",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(Auditor.objects.count(), 1)
        self.auditor.refresh_from_db()
        self.assertEqual(self.auditor.person, self.person2)

    def test_post_delete(self):
        url = resolve_url('parcours_doctoral:config:auditors')
        self.client.force_login(self.das.person.user)
        response = self.client.post(
            url,
            data={
                "form-TOTAL_FORMS": "2",
                "form-INITIAL_FORMS": "2",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
                "form-0-auditor": "",
                "form-1-auditor": "",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(Auditor.objects.count(), 0)
