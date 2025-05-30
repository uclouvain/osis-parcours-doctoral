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

import factory

from parcours_doctoral.auth.roles.adre import AdreSecretary
from parcours_doctoral.auth.roles.cdd_configurator import CddConfigurator
from parcours_doctoral.auth.roles.student import Student


class BaseFactory(factory.django.DjangoModelFactory):
    person = factory.SubFactory('base.tests.factories.person.PersonFactory')


class CddConfiguratorFactory(BaseFactory):
    class Meta:
        model = CddConfigurator

    entity = factory.SubFactory(
        'base.tests.factories.entity.EntityWithVersionFactory',
        organization=None,
    )
    with_child = False


class StudentRoleFactory(BaseFactory):
    class Meta:
        model = Student
        django_get_or_create = ('person',)


class AdreSecretaryRoleFactory(BaseFactory):
    class Meta:
        model = AdreSecretary
        django_get_or_create = ('person',)
