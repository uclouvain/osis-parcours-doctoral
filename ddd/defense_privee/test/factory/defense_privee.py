# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
import uuid

import factory
from factory.fuzzy import FuzzyDate, FuzzyNaiveDateTime

from parcours_doctoral.ddd.defense_privee.domain.model.defense_privee import (
    DefensePrivee,
    DefensePriveeIdentity,
)
from parcours_doctoral.ddd.test.factory.parcours_doctoral import (
    _ParcoursDoctoralIdentityFactory,
)


class _DefensePriveeIdentityFactory(factory.Factory):
    class Meta:
        model = DefensePriveeIdentity
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))


class DefensePriveeFactory(factory.Factory):
    class Meta:
        model = DefensePrivee
        abstract = False

    entity_id = factory.SubFactory(_DefensePriveeIdentityFactory)
    parcours_doctoral_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory)
    est_active = True
    date_heure = FuzzyNaiveDateTime(start_dt=datetime.datetime(2020, 1, 1))
    lieu = factory.Faker('address')
    date_envoi_manuscrit = FuzzyDate(start_date=datetime.date(2020, 1, 1))
    proces_verbal = factory.List(['file-1'])
    canevas_proces_verbal = factory.List(['file-2'])
