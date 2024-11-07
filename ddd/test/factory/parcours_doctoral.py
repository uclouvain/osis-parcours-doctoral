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
import uuid

import factory

from parcours_doctoral.ddd.domain.model._formation import FormationIdentity
from parcours_doctoral.ddd.domain.model._projet import Projet
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoral, ParcoursDoctoralIdentity
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral


class _ParcoursDoctoralIdentityFactory(factory.Factory):
    class Meta:
        model = ParcoursDoctoralIdentity
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))


class _ProjetFactory(factory.Factory):
    class Meta:
        model = Projet
        abstract = False

    titre = factory.Faker('word')
    resume = factory.Faker('sentence')
    langue_redaction_these = 'FR'
    institut_these = factory.LazyFunction(lambda: str(uuid.uuid4()))
    lieu_these = factory.Faker('city')
    deja_commence = False


class _ParcoursDoctoralFactory(factory.Factory):
    class Meta:
        model = ParcoursDoctoral
        abstract = False

    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory)
    statut = ChoixStatutParcoursDoctoral.ADMITTED
    projet = factory.SubFactory(_ProjetFactory)
    cotutelle = None


class ParcoursDoctoralSC3DPMinimaleFactory(_ParcoursDoctoralFactory):
    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP')
    formation_id = FormationIdentity(sigle='SC3DP', annee=2022)
    matricule_doctorant = '1'
    reference = 'r1'


class ParcoursDoctoralPreSC3DPAvecPromoteursEtMembresCADejaApprouvesAccepteeFactory(_ParcoursDoctoralFactory):
    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-pre-SC3DP-promoteurs-membres-deja-approuves')
    formation_id = FormationIdentity(sigle='SC3DP', annee=2022)
    matricule_doctorant = '1'
    reference = 'r2'


class ParcoursDoctoralSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactoryRejeteeCDDFactory(_ParcoursDoctoralFactory):
    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-promoteur-refus-membre-deja-approuve')
    formation_id = FormationIdentity(sigle='SC3DP', annee=2022)
    matricule_doctorant = '2'
    reference = 'r3'


class ParcoursDoctoralSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(_ParcoursDoctoralFactory):
    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-promoteurs-membres-deja-approuves')
    formation_id = FormationIdentity(sigle='SC3DP', annee=2022)
    matricule_doctorant = '3'
    reference = 'r4'