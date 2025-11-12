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
import uuid

import factory

from base.tests.factories.person import generate_global_id
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.autorisation_diffusion_these import (
    AutorisationDiffusionThese,
    AutorisationDiffusionTheseIdentity,
    SignataireAutorisationDiffusionThese,
    SignatureAutorisationDiffusionThese,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.enums import (
    ChoixStatutAutorisationDiffusionThese,
    RoleActeur,
    TypeModalitesDiffusionThese,
)


class AutorisationDiffusionTheseIdentityFactory(factory.Factory):
    class Meta:
        model = AutorisationDiffusionTheseIdentity
        abstract = False

    uuid = factory.LazyFunction(lambda: uuid.uuid4())


class SignatureAutorisationDiffusionTheseFactory(factory.Factory):
    class Meta:
        model = SignatureAutorisationDiffusionThese
        abstract = False


class SignataireAutorisationDiffusionTheseFactory(factory.Factory):
    class Meta:
        model = SignataireAutorisationDiffusionThese
        abstract = False

    matricule = factory.LazyFunction(generate_global_id)
    role = RoleActeur.PROMOTEUR
    uuid = factory.LazyFunction(lambda: uuid.uuid4())
    signature = factory.SubFactory(SignatureAutorisationDiffusionTheseFactory)


class AutorisationDiffusionTheseFactory(factory.Factory):
    class Meta:
        model = AutorisationDiffusionThese
        abstract = False

    entity_id = factory.SubFactory(AutorisationDiffusionTheseIdentityFactory)

    statut = ChoixStatutAutorisationDiffusionThese.DIFFUSION_NON_SOUMISE
    sources_financement = 'Sources'
    resume_anglais = 'Summary in english'
    resume_autre_langue = 'Résumé en français'
    langue_redaction_these = 'FR'
    mots_cles = factory.List(['doctorat', 'informatique'])
    type_modalites_diffusion = TypeModalitesDiffusionThese.ACCES_EMBARGO
    date_embargo = factory.Faker('date')
    limitations_additionnelles_chapitres = 'Limitations pour les chapitres 1 et 2'
    modalites_diffusion_acceptees = 'Modalités acceptées'
    modalites_diffusion_acceptees_le = factory.Faker('date')
    signataires = factory.LazyFunction(lambda: {})
