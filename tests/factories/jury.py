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
import factory

from base.tests.factories.person import PersonFactory
from parcours_doctoral.ddd.jury.domain.model.enums import (
    GenreMembre,
    RoleJury,
    TitreMembre,
)
from parcours_doctoral.models.jury import JuryMember
from parcours_doctoral.tests.factories.supervision import (
    ExternalPromoterFactory,
    PromoterFactory,
)


class _JuryMemberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = JuryMember

    parcours_doctoral = factory.SubFactory(
        'parcours_doctoral.tests.factories.parcours_doctoral.ParcoursDoctoralFactory',
    )
    role = RoleJury.MEMBRE.name
    other_institute = ''
    promoter = None
    person = None
    institute = ''
    country = None
    last_name = ''
    first_name = ''
    title = ''
    non_doctor_reason = ''
    gender = ''
    email = ''


class JuryMemberFactory(_JuryMemberFactory):
    person = factory.SubFactory(PersonFactory)


class ExternalJuryMemberFactory(_JuryMemberFactory):
    other_institute = ''
    promoter = None
    person = None
    institute = 'institute'
    country = factory.SubFactory('reference.tests.factories.country.CountryFactory')
    last_name = 'last name'
    first_name = 'first_name'
    title = TitreMembre.DOCTEUR.name
    non_doctor_reason = ''
    gender = GenreMembre.AUTRE.name
    email = 'email@example.org'


class JuryMemberWithInternalPromoterFactory(_JuryMemberFactory):
    promoter = factory.SubFactory(PromoterFactory)


class JuryMemberWithExternalPromoterFactory(_JuryMemberFactory):
    promoter = factory.SubFactory(ExternalPromoterFactory)
