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
from django.test import TestCase

from parcours_doctoral.infrastructure.mixins.notification import NotificationMixin
from parcours_doctoral.tests.factories.jury import (
    ExternalJuryMemberFactory,
    JuryMemberFactory,
    JuryMemberWithExternalPromoterFactory,
    JuryMemberWithInternalPromoterFactory,
)


class NotificationTestCase(TestCase):
    def test_get_jury_member_info_with_internal_member(self):
        jury_member = JuryMemberFactory(
            person__first_name='John',
            person__last_name='Poe',
            person__email='john.poe@test.be',
        )
        jury_member_info = NotificationMixin.get_jury_member_info(jury_member=jury_member)
        self.assertEqual(jury_member_info['person'], jury_member.person)
        self.assertEqual(jury_member_info['first_name'], jury_member.person.first_name)
        self.assertEqual(jury_member_info['last_name'], jury_member.person.last_name)
        self.assertEqual(jury_member_info['language'], jury_member.person.language)
        self.assertEqual(jury_member_info['email'], jury_member.person.email)

    def test_get_jury_member_info_with_external_member(self):
        external_jury_member = ExternalJuryMemberFactory(
            first_name='Jim',
            last_name='Poe',
            email='jim.poe@test.be',
        )
        jury_member_info = NotificationMixin.get_jury_member_info(jury_member=external_jury_member)
        self.assertEqual(jury_member_info['person'], None)
        self.assertEqual(jury_member_info['first_name'], external_jury_member.first_name)
        self.assertEqual(jury_member_info['last_name'], external_jury_member.last_name)
        self.assertEqual(jury_member_info['language'], '')
        self.assertEqual(jury_member_info['email'], external_jury_member.email)

    def test_get_jury_member_info_with_internal_promoter_member(self):
        jury_member_with_internal_promoter = JuryMemberWithInternalPromoterFactory(
            promoter__actor_ptr__person__first_name='Jane',
            promoter__actor_ptr__person__last_name='Doe',
            promoter__actor_ptr__person__email='jane.doe@test.be',
        )
        jury_member_info = NotificationMixin.get_jury_member_info(jury_member=jury_member_with_internal_promoter)
        self.assertEqual(jury_member_info['person'], jury_member_with_internal_promoter.promoter.person)
        self.assertEqual(jury_member_info['first_name'], jury_member_with_internal_promoter.promoter.person.first_name)
        self.assertEqual(jury_member_info['last_name'], jury_member_with_internal_promoter.promoter.person.last_name)
        self.assertEqual(jury_member_info['language'], jury_member_with_internal_promoter.promoter.person.language)
        self.assertEqual(jury_member_info['email'], jury_member_with_internal_promoter.promoter.person.email)

    def test_get_jury_member_info_with_external_promoter_member(self):
        jury_member_with_external_promoter = JuryMemberWithExternalPromoterFactory(
            promoter__first_name='Tom',
            promoter__last_name='Doe',
            promoter__email='tom.doe@test.be',
        )
        jury_member_info = NotificationMixin.get_jury_member_info(jury_member=jury_member_with_external_promoter)
        self.assertEqual(jury_member_info['person'], None)
        self.assertEqual(jury_member_info['first_name'], jury_member_with_external_promoter.promoter.first_name)
        self.assertEqual(jury_member_info['last_name'], jury_member_with_external_promoter.promoter.last_name)
        self.assertEqual(jury_member_info['language'], jury_member_with_external_promoter.promoter.language)
        self.assertEqual(jury_member_info['email'], jury_member_with_external_promoter.promoter.email)
