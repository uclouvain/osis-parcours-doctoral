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
import json

from django.test import TestCase
from django.urls import reverse
from osis_comment.models import CommentEntry

from admission.tests.factories.comment import CommentEntryFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ENTITY_CDE, ENTITY_CDSS
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory


class CommentsViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        # First entity
        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)

        second_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=second_doctoral_commission, acronym=ENTITY_CDSS)

        # Create doctorates
        cls.doctorate = ParcoursDoctoralFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
        )

        # Create users
        cls.manager = ProgramManagerFactory(education_group=cls.doctorate.training.education_group).person
        cls.other_manager = ProgramManagerFactory().person

        # Create url
        cls.url = reverse(
            'parcours_doctoral:comments',
            args=[str(cls.doctorate.uuid)],
        )

    def test_only_related_manager_is_allowed(self):
        self.client.force_login(self.manager.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        self.client.force_login(self.other_manager.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)


class CommentsApiViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        # First entity
        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)

        second_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=second_doctoral_commission, acronym=ENTITY_CDSS)

        # Create doctorates
        cls.doctorate = ParcoursDoctoralFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
        )

        # Create users
        cls.manager_1 = ProgramManagerFactory(education_group=cls.doctorate.training.education_group).person
        cls.manager_2 = ProgramManagerFactory(education_group=cls.doctorate.training.education_group).person
        cls.other_manager = ProgramManagerFactory().person

        # Create url
        cls.base_url = 'parcours_doctoral:comments-api'
        cls.url = reverse(cls.base_url, args=[str(cls.doctorate.uuid)])

    def test_list_of_comments(self):
        self.client.force_login(self.manager_1.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        results = response.json()['results']

        self.assertEqual(len(results), 0)

        # Add a comment
        new_comment = CommentEntryFactory(
            object_uuid=self.doctorate.uuid,
            author=self.manager_1,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        results = response.json()['results']

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(new_comment.uuid))

        self.client.force_login(self.other_manager.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_create_a_comment(self):
        self.client.force_login(self.manager_1.user)

        response = self.client.post(
            self.url,
            data=json.dumps({'comment': 'My original content'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)

        new_comment = CommentEntry.objects.filter(
            object_uuid=self.doctorate.uuid,
        )

        self.assertEqual(len(new_comment), 1)
        self.assertEqual(new_comment[0].author, self.manager_1)
        self.assertEqual(new_comment[0].content, 'My original content')

        self.client.force_login(self.other_manager.user)

        response = self.client.post(
            self.url,
            data=json.dumps({'comment': 'My original content'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)

    def test_update_a_comment(self):
        self.client.force_login(self.manager_1.user)

        comment = CommentEntryFactory(
            object_uuid=self.doctorate.uuid,
            author=self.manager_1,
            content='My original content',
        )

        update_url = reverse(self.base_url, args=[str(self.doctorate.uuid), str(comment.uuid)])

        response = self.client.put(
            update_url,
            data=json.dumps({'comment': 'My new content'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)

        comment.refresh_from_db()

        self.assertEqual(comment.content, 'My new content')

        self.client.force_login(self.other_manager.user)

        response = self.client.put(
            update_url,
            data=json.dumps({'comment': 'My new content'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.manager_2.user)

        response = self.client.put(
            update_url,
            data=json.dumps({'comment': 'My new content'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)

    def test_delete_a_comment(self):
        self.client.force_login(self.manager_1.user)

        comment = CommentEntryFactory(
            object_uuid=self.doctorate.uuid,
            author=self.manager_1,
            content='My original content',
        )

        delete_url = reverse(self.base_url, args=[str(self.doctorate.uuid), str(comment.uuid)])

        response = self.client.delete(delete_url)

        self.assertEqual(response.status_code, 204)

        self.assertFalse(CommentEntry.objects.filter(uuid=comment.uuid).exists())

        comment = CommentEntryFactory(
            object_uuid=self.doctorate.uuid,
            author=self.manager_1,
            content='My original content',
        )

        delete_url = reverse(self.base_url, args=[str(self.doctorate.uuid), str(comment.uuid)])

        self.client.force_login(self.other_manager.user)

        response = self.client.delete(delete_url)

        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.manager_2.user)

        response = self.client.delete(delete_url)

        self.assertEqual(response.status_code, 403)
