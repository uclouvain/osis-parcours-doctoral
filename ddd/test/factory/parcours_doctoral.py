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
import itertools
import uuid

import factory

from base.tests.factories.person import generate_global_id
from parcours_doctoral.ddd.domain.model._cotutelle import Cotutelle, pas_de_cotutelle
from parcours_doctoral.ddd.domain.model._experience_precedente_recherche import aucune_experience_precedente_recherche
from parcours_doctoral.ddd.domain.model._financement import Financement, financement_non_rempli
from parcours_doctoral.ddd.domain.model._formation import FormationIdentity
from parcours_doctoral.ddd.domain.model._projet import Projet, projet_non_rempli
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral, ChoixTypeFinancement
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoral, ParcoursDoctoralIdentity

REFERENCE_MEMORY_ITERATOR = itertools.count()


class _ParcoursDoctoralIdentityFactory(factory.Factory):
    class Meta:
        model = ParcoursDoctoralIdentity
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))



class _CotutelleFactory(factory.Factory):
    demande_ouverture = factory.LazyFunction(lambda: [str(uuid.uuid4())])

    class Meta:
        model = Cotutelle
        abstract = False


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
    documents = factory.LazyFunction(lambda: [str(uuid.uuid4())])
    proposition_programme_doctoral = factory.LazyFunction(lambda: [str(uuid.uuid4())])


class _FormationIdentityFactory(factory.Factory):
    class Meta:
        model = FormationIdentity
        abstract = False

    sigle = factory.Sequence(lambda n: 'SIGLE%02d' % n)
    annee = factory.fuzzy.FuzzyInteger(1999, 2099)


class _FinancementFactory(factory.Factory):
    class Meta:
        model = Financement
        abstract = False

    type = ChoixTypeFinancement.SELF_FUNDING
    duree_prevue = 10
    temps_consacre = 10


class _ParcoursDoctoralFactory(factory.Factory):
    class Meta:
        model = ParcoursDoctoral
        abstract = False

    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory)
    matricule_doctorant = factory.LazyFunction(generate_global_id)
    reference = factory.Iterator(REFERENCE_MEMORY_ITERATOR)
    formation_id = factory.SubFactory(_FormationIdentityFactory)
    statut = ChoixStatutParcoursDoctoral.ADMITTED
    projet = factory.SubFactory(_ProjetFactory)
    financement = factory.SubFactory(_FinancementFactory)
    experience_precedente_recherche = aucune_experience_precedente_recherche
    cotutelle = None


class ParcoursDoctoralSC3DPMinimaleFactory(_ParcoursDoctoralFactory):
    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP')
    formation_id = FormationIdentity(sigle='SC3DP', annee=2022)
    matricule_doctorant = '1'
    reference = 'r1'
    cotutelle = factory.SubFactory(
        _CotutelleFactory,
        motivation="Runs in family",
        institution_fwb=False,
        institution="MIT",
    )


class ParcoursDoctoralECGE3DPMinimaleFactory(_ParcoursDoctoralFactory):
    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-ECGE3DP')
    formation_id = FormationIdentity(sigle='ECGE3DP', annee=2020)
    matricule_doctorant = '0123456789'


class ParcoursDoctoralESP3DPMinimaleFactory(_ParcoursDoctoralFactory):
    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-ESP3DP')
    formation_id = FormationIdentity(sigle='ESP3DP', annee=2020)
    matricule_doctorant = '0123456789'


class ParcoursDoctoralSC3DPMinimaleSansDetailProjetFactory(ParcoursDoctoralSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-no-project')
    projet = projet_non_rempli
    cotutelle = pas_de_cotutelle


class ParcoursDoctoralSC3DPMinimaleSansFinancementFactory(ParcoursDoctoralSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-no-financement')
    financement = financement_non_rempli
    cotutelle = pas_de_cotutelle


class ParcoursDoctoralSC3DPMinimaleSansCotutelleFactory(ParcoursDoctoralSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-cotutelle-indefinie')
    cotutelle = None


class ParcoursDoctoralSC3DPMinimaleCotutelleSansPromoteurExterneFactory(ParcoursDoctoralSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-cotutelle-sans-promoteur-externe')
    cotutelle = factory.SubFactory(
        _CotutelleFactory,
        motivation="Runs in family",
        institution_fwb=False,
        institution="MIT",
    )


class ParcoursDoctoralSC3DPMinimaleCotutelleAvecPromoteurExterneFactory(ParcoursDoctoralSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-cotutelle-avec-promoteur-externe')
    cotutelle = factory.SubFactory(
        _CotutelleFactory,
        motivation="Runs in family",
        institution_fwb=False,
        institution="MIT",
    )


class ParcoursDoctoralPreSC3DPAvecPromoteursEtMembresCADejaApprouvesAccepteeFactory(_ParcoursDoctoralFactory):
    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-pre-SC3DP-promoteurs-membres-deja-approuves')
    formation_id = FormationIdentity(sigle='SC3DP', annee=2022)
    matricule_doctorant = '1'
    reference = 'r2'
    cotutelle = pas_de_cotutelle


class ParcoursDoctoralSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactoryRejeteeCDDFactory(_ParcoursDoctoralFactory):
    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-promoteur-refus-membre-deja-approuve')
    formation_id = FormationIdentity(sigle='SC3DP', annee=2022)
    matricule_doctorant = '2'
    reference = 'r3'
    cotutelle = pas_de_cotutelle


class ParcoursDoctoralSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(_ParcoursDoctoralFactory):
    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-promoteurs-membres-deja-approuves')
    formation_id = FormationIdentity(sigle='SC3DP', annee=2022)
    matricule_doctorant = '3'
    reference = 'r4'


class ParcoursDoctoralSC3DPAvecMembresFactory(ParcoursDoctoralSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-promoteur-membre')


class ParcoursDoctoralSC3DPAvecMembresEtCotutelleFactory(ParcoursDoctoralSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-promoteur-membre-cotutelle')
    matricule_doctorant = 'candidat'
    cotutelle = factory.SubFactory(
        _CotutelleFactory,
        motivation="Runs in family",
        institution_fwb=False,
        institution="MIT",
    )


class ParcoursDoctoralSC3DPAvecMembresInvitesFactory(ParcoursDoctoralSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-membres-invites')


class ParcoursDoctoralSC3DPSansPromoteurFactory(ParcoursDoctoralSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-sans-promoteur')


class ParcoursDoctoralSC3DPSansPromoteurReferenceFactory(ParcoursDoctoralSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-sans-promoteur-reference')


class ParcoursDoctoralSC3DPSansMembreCAFactory(ParcoursDoctoralSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-sans-membre_CA')
    matricule_doctorant = '0123456789'


class ParcoursDoctoralSC3DPAvecPromoteurDejaApprouveFactory(ParcoursDoctoralSC3DPMinimaleFactory):
    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-promoteur-deja-approuve')
    cotutelle = pas_de_cotutelle


class ParcoursDoctoralSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactory(
    ParcoursDoctoralSC3DPMinimaleFactory
):
    entity_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-promoteur-refus-membre-deja-approuve')
    matricule_doctorant = 'candidat'
