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
import uuid
from typing import List

import factory

from parcours_doctoral.ddd.domain.model._membre_CA import MembreCAIdentity
from parcours_doctoral.ddd.domain.model._promoteur import PromoteurIdentity
from parcours_doctoral.ddd.domain.model._signature_membre_CA import SignatureMembreCA
from parcours_doctoral.ddd.domain.model._signature_promoteur import SignaturePromoteur
from parcours_doctoral.ddd.domain.model.enums import (
    ChoixEtatSignature,
    ChoixStatutSignatureGroupeDeSupervision,
)
from parcours_doctoral.ddd.domain.model.groupe_de_supervision import (
    GroupeDeSupervision,
    GroupeDeSupervisionIdentity,
)
from parcours_doctoral.ddd.test.factory.parcours_doctoral import (
    _ParcoursDoctoralIdentityFactory,
)


class _PromoteurIdentityFactory(factory.Factory):
    class Meta:
        model = PromoteurIdentity
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))


class _MembreCAIdentityFactory(factory.Factory):
    class Meta:
        model = MembreCAIdentity
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))


class _SignaturePromoteurFactory(factory.Factory):
    class Meta:
        model = SignaturePromoteur
        abstract = False

    promoteur_id = factory.SubFactory(_PromoteurIdentityFactory)


class _SignatureMembreCAFactory(factory.Factory):
    class Meta:
        model = SignatureMembreCA
        abstract = False

    membre_CA_id = factory.SubFactory(_MembreCAIdentityFactory)


class _GroupeDeSupervisionIdentityFactory(factory.Factory):
    class Meta:
        model = GroupeDeSupervisionIdentity
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))


class _GroupeDeSupervisionFactory(factory.Factory):
    class Meta:
        model = GroupeDeSupervision
        abstract = False

    entity_id = factory.SubFactory(_GroupeDeSupervisionIdentityFactory)
    parcours_doctoral_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory)
    signatures_promoteurs = factory.LazyFunction(list)
    signatures_membres_CA = factory.LazyFunction(list)
    promoteur_reference_id = factory.LazyAttribute(
        lambda o: getattr(next(iter(o.signatures_promoteurs), None), 'promoteur_id', None)
    )


class GroupeDeSupervisionSC3DPFactory(_GroupeDeSupervisionFactory):
    parcours_doctoral_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP')


class GroupeDeSupervisionSC3DPCotutelleIndefinieFactory(_GroupeDeSupervisionFactory):
    parcours_doctoral_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-cotutelle-indefinie')


class GroupeDeSupervisionSC3DPPreAdmissionFactory(_GroupeDeSupervisionFactory):
    parcours_doctoral_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-pre-admission')


class GroupeDeSupervisionSC3DPAvecPromoteurEtMembreFactory(_GroupeDeSupervisionFactory):
    parcours_doctoral_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-promoteur-membre')
    signatures_promoteurs = factory.LazyFunction(
        lambda: [_SignaturePromoteurFactory(promoteur_id__uuid='promoteur-SC3DP')]
    )
    signatures_membres_CA = factory.LazyFunction(
        lambda: [
            _SignatureMembreCAFactory(membre_CA_id__uuid='membre-ca-SC3DP', etat=ChoixEtatSignature.INVITED),
            _SignatureMembreCAFactory(membre_CA_id__uuid='membre-ca-SC3DP2', etat=ChoixEtatSignature.INVITED),
        ]
    )


class GroupeDeSupervisionSC3DPAvecPromoteurEtMembreEtCotutelleFactory(_GroupeDeSupervisionFactory):
    parcours_doctoral_id = factory.SubFactory(
        _ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-promoteur-membre-cotutelle'
    )
    signatures_promoteurs = factory.LazyFunction(
        lambda: [
            _SignaturePromoteurFactory(promoteur_id__uuid='promoteur-SC3DP-externe'),
            _SignaturePromoteurFactory(promoteur_id__uuid='promoteur-SC3DP'),
        ]
    )
    signatures_membres_CA = factory.LazyFunction(
        lambda: [
            _SignatureMembreCAFactory(membre_CA_id__uuid='membre-ca-SC3DP', etat=ChoixEtatSignature.INVITED),
            _SignatureMembreCAFactory(membre_CA_id__uuid='membre-ca-SC3DP2', etat=ChoixEtatSignature.INVITED),
        ]
    )


class GroupeDeSupervisionSC3DPCotutelleSansPromoteurExterneFactory(_GroupeDeSupervisionFactory):
    parcours_doctoral_id = factory.SubFactory(
        _ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-cotutelle-sans-promoteur-externe'
    )
    signatures_promoteurs = factory.LazyFunction(
        lambda: [_SignaturePromoteurFactory(promoteur_id__uuid='promoteur-SC3DP')]
    )
    signatures_membres_CA = factory.LazyFunction(
        lambda: [
            _SignatureMembreCAFactory(membre_CA_id__uuid='membre-ca-SC3DP', etat=ChoixEtatSignature.INVITED),
            _SignatureMembreCAFactory(membre_CA_id__uuid='membre-ca-SC3DP2', etat=ChoixEtatSignature.INVITED),
        ]
    )


class GroupeDeSupervisionSC3DPCotutelleAvecPromoteurExterneFactory(_GroupeDeSupervisionFactory):
    parcours_doctoral_id = factory.SubFactory(
        _ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-cotutelle-avec-promoteur-externe'
    )
    signatures_promoteurs = factory.LazyFunction(
        lambda: [
            _SignaturePromoteurFactory(promoteur_id__uuid='promoteur-SC3DP'),
            _SignaturePromoteurFactory(promoteur_id__uuid='promoteur-SC3DP-externe'),
        ]
    )
    signatures_membres_CA = factory.LazyFunction(
        lambda: [
            _SignatureMembreCAFactory(membre_CA_id__uuid='membre-ca-SC3DP', etat=ChoixEtatSignature.INVITED),
            _SignatureMembreCAFactory(membre_CA_id__uuid='membre-ca-SC3DP2', etat=ChoixEtatSignature.INVITED),
        ]
    )


class GroupeDeSupervisionSC3DPAvecPromoteurEtMembreEtProjetIncompletFactory(_GroupeDeSupervisionFactory):
    parcours_doctoral_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-no-project')
    signatures_promoteurs = factory.LazyFunction(
        lambda: [_SignaturePromoteurFactory(promoteur_id__uuid='promoteur-SC3DP')]
    )
    signatures_membres_CA = factory.LazyFunction(
        lambda: [
            _SignatureMembreCAFactory(membre_CA_id__uuid='membre-ca-SC3DP', etat=ChoixEtatSignature.INVITED),
            _SignatureMembreCAFactory(membre_CA_id__uuid='membre-ca-SC3DP2', etat=ChoixEtatSignature.INVITED),
        ]
    )


class GroupeDeSupervisionSC3DPAvecPromoteurEtMembreEtFinancementIncompletFactory(_GroupeDeSupervisionFactory):
    parcours_doctoral_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-no-financement')
    signatures_promoteurs = factory.LazyFunction(
        lambda: [_SignaturePromoteurFactory(promoteur_id__uuid='promoteur-SC3DP')]
    )
    signatures_membres_CA = factory.LazyFunction(
        lambda: [
            _SignatureMembreCAFactory(membre_CA_id__uuid='membre-ca-SC3DP', etat=ChoixEtatSignature.INVITED),
            _SignatureMembreCAFactory(membre_CA_id__uuid='membre-ca-SC3DP2', etat=ChoixEtatSignature.INVITED),
        ]
    )


class GroupeDeSupervisionSC3DPAvecMembresInvitesFactory(_GroupeDeSupervisionFactory):
    parcours_doctoral_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-membres-invites')
    signatures_promoteurs = factory.LazyFunction(
        lambda: [_SignaturePromoteurFactory(promoteur_id__uuid='promoteur-SC3DP', etat=ChoixEtatSignature.INVITED)]
    )
    signatures_membres_CA = factory.LazyFunction(
        lambda: [
            _SignatureMembreCAFactory(membre_CA_id__uuid='membre-ca-SC3DP-invite', etat=ChoixEtatSignature.INVITED),
            _SignatureMembreCAFactory(membre_CA_id__uuid='membre-ca-SC3DP', etat=ChoixEtatSignature.INVITED),
        ]
    )


class GroupeDeSupervisionSC3DPSansPromoteurFactory(_GroupeDeSupervisionFactory):
    parcours_doctoral_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-sans-promoteur')
    signatures_promoteurs: List[SignaturePromoteur] = []
    signatures_membres_CA = factory.LazyFunction(
        lambda: [
            _SignatureMembreCAFactory(membre_CA_id__uuid='membre-ca-SC3DP'),
            _SignatureMembreCAFactory(membre_CA_id__uuid='membre-ca-SC3DP2'),
        ]
    )


class GroupeDeSupervisionSC3DPSansPromoteurReferenceFactory(GroupeDeSupervisionSC3DPAvecPromoteurEtMembreFactory):
    parcours_doctoral_id = factory.SubFactory(
        _ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-sans-promoteur-reference'
    )
    promoteur_reference_id = None


class GroupeDeSupervisionSC3DPSansMembresCAFactory(_GroupeDeSupervisionFactory):
    parcours_doctoral_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-sans-membre_CA')
    signatures_promoteurs = factory.LazyFunction(
        lambda: [
            _SignaturePromoteurFactory(promoteur_id__uuid='promoteur-SC3DP-unique', etat=ChoixEtatSignature.INVITED),
        ]
    )
    signatures_membres_CA: List[SignatureMembreCA] = []


class GroupeDeSupervisionSC3DPAvecPromoteurDejaApprouveEtAutrePromoteurFactory(_GroupeDeSupervisionFactory):
    parcours_doctoral_id = factory.SubFactory(
        _ParcoursDoctoralIdentityFactory, uuid='uuid-SC3DP-promoteur-deja-approuve'
    )
    signatures_promoteurs = factory.LazyFunction(
        lambda: [
            _SignaturePromoteurFactory(promoteur_id__uuid='promoteur-SC3DP', etat=ChoixEtatSignature.INVITED),
            _SignaturePromoteurFactory(
                promoteur_id__uuid='promoteur-SC3DP-deja-approuve',
                etat=ChoixEtatSignature.APPROVED,
            ),
        ]
    )
    signatures_membres_CA = factory.LazyFunction(
        lambda: [
            _SignatureMembreCAFactory(membre_CA_id__uuid='membre-ca-SC3DP', etat=ChoixEtatSignature.INVITED),
            _SignatureMembreCAFactory(membre_CA_id__uuid='membre-ca-SC3DP2', etat=ChoixEtatSignature.INVITED),
        ]
    )


class GroupeDeSupervisionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(_GroupeDeSupervisionFactory):
    parcours_doctoral_id = factory.SubFactory(
        _ParcoursDoctoralIdentityFactory,
        uuid='uuid-SC3DP-promoteurs-membres-deja-approuves',
    )
    signatures_promoteurs = factory.LazyFunction(
        lambda: [
            _SignaturePromoteurFactory(
                promoteur_id__uuid='promoteur-SC3DP-deja-approuve',
                etat=ChoixEtatSignature.APPROVED,
            ),
        ]
    )
    signatures_membres_CA = factory.LazyFunction(
        lambda: [
            _SignatureMembreCAFactory(membre_CA_id__uuid='membre-ca-SC3DP', etat=ChoixEtatSignature.APPROVED),
            _SignatureMembreCAFactory(membre_CA_id__uuid='membre-ca-SC3DP2', etat=ChoixEtatSignature.APPROVED),
        ]
    )
    statut_signature = ChoixStatutSignatureGroupeDeSupervision.SIGNING_IN_PROGRESS


class GroupeDeSupervisionSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactory(_GroupeDeSupervisionFactory):
    parcours_doctoral_id = factory.SubFactory(
        _ParcoursDoctoralIdentityFactory,
        uuid='uuid-SC3DP-promoteur-refus-membre-deja-approuve',
    )
    signatures_promoteurs = factory.LazyFunction(
        lambda: [
            _SignaturePromoteurFactory(
                promoteur_id__uuid='promoteur-SC3DP',
                etat=ChoixEtatSignature.DECLINED,
            ),
        ]
    )
    signatures_membres_CA = factory.LazyFunction(
        lambda: [
            _SignatureMembreCAFactory(membre_CA_id__uuid='membre-ca-SC3DP', etat=ChoixEtatSignature.APPROVED),
            _SignatureMembreCAFactory(membre_CA_id__uuid='membre-ca-SC3DP2', etat=ChoixEtatSignature.APPROVED),
        ]
    )


class GroupeDeSupervisionPreSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(
    GroupeDeSupervisionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
):
    parcours_doctoral_id = factory.SubFactory(
        _ParcoursDoctoralIdentityFactory,
        uuid='uuid-pre-SC3DP-promoteurs-membres-deja-approuves',
    )


class GroupeDeSupervisionConfirmeeSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(
    GroupeDeSupervisionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
):
    parcours_doctoral_id = factory.SubFactory(
        _ParcoursDoctoralIdentityFactory,
        uuid='uuid-SC3DP-confirmee',
    )
