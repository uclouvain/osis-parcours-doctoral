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
import uuid

import factory

from parcours_doctoral.ddd.epreuve_confirmation.domain.model._demande_prolongation import (
    DemandeProlongation,
)
from parcours_doctoral.ddd.epreuve_confirmation.domain.model.epreuve_confirmation import (
    EpreuveConfirmation,
    EpreuveConfirmationIdentity,
)
from parcours_doctoral.ddd.test.factory.parcours_doctoral import (
    _ParcoursDoctoralIdentityFactory,
)


class _EpreuveConfirmationIdentityFactory(factory.Factory):
    class Meta:
        model = EpreuveConfirmationIdentity
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))


class _EpreuveConfirmationFactory(factory.Factory):
    class Meta:
        model = EpreuveConfirmation
        abstract = False

    entity_id = factory.SubFactory(_EpreuveConfirmationIdentityFactory)
    date_limite = factory.Faker('future_date')


class EpreuveConfirmation0DoctoratSC3DPFactory(_EpreuveConfirmationFactory):
    entity_id = factory.SubFactory(_EpreuveConfirmationIdentityFactory, uuid='c0')
    parcours_doctoral_id = factory.SubFactory(
        _ParcoursDoctoralIdentityFactory, uuid='uuid-pre-SC3DP-promoteurs-membres-deja-approuves'
    )
    date_limite = datetime.date(2022, 12, 5)
    date = datetime.date(2022, 4, 1)


class EpreuveConfirmation1DoctoratSC3DPFactory(_EpreuveConfirmationFactory):
    entity_id = factory.SubFactory(_EpreuveConfirmationIdentityFactory, uuid='c1')
    parcours_doctoral_id = factory.SubFactory(
        _ParcoursDoctoralIdentityFactory, uuid='uuid-pre-SC3DP-promoteurs-membres-deja-approuves'
    )
    date_limite = datetime.date(2022, 4, 5)


class EpreuveConfirmation2DoctoratSC3DPFactory(_EpreuveConfirmationFactory):
    entity_id = factory.SubFactory(_EpreuveConfirmationIdentityFactory, uuid='c2')
    parcours_doctoral_id = factory.SubFactory(
        _ParcoursDoctoralIdentityFactory, uuid='uuid-pre-SC3DP-promoteurs-membres-deja-approuves'
    )
    date = datetime.date(2022, 1, 1)
    date_limite = datetime.date(2022, 1, 5)
    demande_prolongation = DemandeProlongation(
        justification_succincte='Ma justification',
        nouvelle_echeance=datetime.date(2023, 1, 1),
    )
    proces_verbal_ca = factory.LazyFunction(lambda: [str(uuid.uuid4())])


class EpreuveConfirmationDoctoratSC3DPRefusFactory(_EpreuveConfirmationFactory):
    entity_id = factory.SubFactory(_EpreuveConfirmationIdentityFactory, uuid='c10')
    parcours_doctoral_id = factory.SubFactory(
        _ParcoursDoctoralIdentityFactory,
        uuid='uuid-SC3DP-promoteur-refus-membre-deja-approuve-refus',
    )
    date_limite = datetime.date(2022, 4, 5)
