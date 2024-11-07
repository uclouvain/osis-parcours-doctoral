# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
import datetime

from django.core.cache import cache
from django.test import TestCase

from parcours_doctoral.utils import get_cached_parcours_doctoral_perm_obj
from parcours_doctoral.models.confirmation_paper import confirmation_paper_directory_path
from parcours_doctoral.tests.factories.confirmation_paper import ConfirmationPaperFactory
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory


class ConfirmationPaperTestCase(TestCase):
    def setUp(self):
        self.parcours_doctoral = ParcoursDoctoralFactory()
        self.confirmation_paper = ConfirmationPaperFactory(
            parcours_doctoral=self.parcours_doctoral,
            confirmation_date=datetime.date(2022, 4, 1),
            confirmation_deadline=datetime.date(2022, 4, 5),
        )

    def test_valid_upload_to(self):
        self.assertEqual(
            confirmation_paper_directory_path(self.confirmation_paper, 'my_file.pdf'),
            'parcours_doctoral/{}/{}/confirmation/{}/my_file.pdf'.format(
                self.parcours_doctoral.student.uuid,
                self.parcours_doctoral.uuid,
                self.confirmation_paper.uuid,
            ),
        )

    def test_permission_cache_dropped_on_training_save(self):
        self.assertEqual(get_cached_parcours_doctoral_perm_obj(self.parcours_doctoral.uuid), self.parcours_doctoral)
        self.assertIsNotNone(cache.get(f"parcours_doctoral_permission_{self.parcours_doctoral.uuid}"))
        self.parcours_doctoral.training.save()
        self.assertIsNone(cache.get(f"parcours_doctoral_permission_{self.parcours_doctoral.uuid}"))

    def test_permission_cache_dropped_on_student_save(self):
        self.assertEqual(get_cached_parcours_doctoral_perm_obj(self.parcours_doctoral.uuid), self.parcours_doctoral)
        self.assertIsNotNone(cache.get(f"parcours_doctoral_permission_{self.parcours_doctoral.uuid}"))
        self.parcours_doctoral.student.save()
        self.assertIsNone(cache.get(f"parcours_doctoral_permission_{self.parcours_doctoral.uuid}"))
