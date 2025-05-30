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
import sys
import uuid

import factory

from parcours_doctoral.ddd.formation import dtos
from parcours_doctoral.ddd.formation.domain.model.activite import (
    Activite,
    ActiviteIdentity,
)
from parcours_doctoral.ddd.formation.domain.model.enums import (
    CategorieActivite,
    ChoixComiteSelection,
    ContexteFormation,
)
from parcours_doctoral.ddd.test.factory.parcours_doctoral import (
    _ParcoursDoctoralIdentityFactory,
)


class CommunicationDTOFactory(factory.Factory):
    class Meta:
        model = dtos.CommunicationDTO
        abstract = False

    type_activite = 'test'
    type_communication = 'test'
    nom = 'test'
    date = 'test'
    pays = 'test'
    ville = 'test'
    institution_organisatrice = 'test'
    titre = 'test'
    comite_selection = ChoixComiteSelection.NO
    attestation_communication = ['test']


class ConferenceDTOFactory(factory.Factory):
    class Meta:
        model = dtos.ConferenceDTO
        abstract = False

    type = "test"
    nom_manifestation = "test"
    date_debut = "test"
    date_fin = "test"
    nombre_jours = "test"
    pays = "test"
    ville = "test"
    institution_organisatrice = "test"
    certificat_participation = ["test"]


class ConferenceCommunicationDTOFactory(factory.Factory):
    class Meta:
        model = dtos.ConferenceCommunicationDTO
        abstract = False

    type = "test"
    titre = "test"
    comite_selection = "test"
    preuve_acceptation = "test"
    attestation_communication = "test"


class ConferencePublicationDTOFactory(factory.Factory):
    class Meta:
        model = dtos.ConferencePublicationDTO
        abstract = False

    type = "test"
    intitule = "test"
    auteurs = "test"
    role = "test"
    comite_selection = "test"
    nom_revue_maison_edition = "test"
    preuve_acceptation = "test"
    date = "test"
    statut_publication = "test"


class PublicationDTOFactory(factory.Factory):
    class Meta:
        model = dtos.PublicationDTO
        abstract = False

    type = "test"
    intitule = "test"
    date = "test"
    auteurs = "test"
    role = "test"
    statut_publication = "test"
    preuve_acceptation = "test"


class ResidencyCommunicationDTOFactory(factory.Factory):
    class Meta:
        model = dtos.SejourCommunicationDTO
        abstract = False

    type_activite = "test"
    type_communication = "test"
    nom = "test"
    date = "test"
    institution_organisatrice = "test"
    titre_communication = "test"
    attestation_communication = "test"


class ResidencyDTOFactory(factory.Factory):
    class Meta:
        model = dtos.SejourDTO
        abstract = False

    type = "test"
    description = "test"
    date_debut = "test"
    date_fin = "test"
    pays = "test"
    ville = "test"


class SeminarDTOFactory(factory.Factory):
    class Meta:
        model = dtos.SeminaireDTO
        abstract = False

    type = "test"
    nom = "test"
    date_debut = "test"
    date_fin = "test"
    attestation_participation = "test"
    volume_horaire = "test"
    volume_horaire_type = "hours"
    pays = "test"
    institution_organisatrice = "test"


class ServiceDTOFactory(factory.Factory):
    class Meta:
        model = dtos.ServiceDTO
        abstract = False

    type = "test"
    nom = "test"
    date_debut = "test"
    date_fin = "test"
    institution = "test"
    volume_horaire = "test"


class VaeDTOFactory(factory.Factory):
    class Meta:
        model = dtos.ValorisationDTO
        abstract = False

    intitule = "test"
    description = "test"
    preuve = ["test"]
    cv = ["test"]


class SeminarCommunicationDTOFactory(factory.Factory):
    class Meta:
        model = dtos.SeminaireCommunicationDTO
        abstract = False

    date = "test"
    titre_communication = "test"
    orateur_oratrice = "test"


class CourseDTOFactory(factory.Factory):
    class Meta:
        model = dtos.CoursDTO
        abstract = False

    avec_evaluation = False
    type = "test"
    nom = "test"
    institution = "test"
    date_debut = "test"
    date_fin = "test"
    volume_horaire = "test"
    certificat = ["test"]


class PaperDTOFactory(factory.Factory):
    class Meta:
        model = dtos.EpreuveDTO
        abstract = False

    type = "CONFIRMATION_PAPER"


class UclCourseDTOFactory(factory.Factory):
    class Meta:
        model = dtos.CoursUclDTO
        abstract = False

    contexte = ContexteFormation.DOCTORAL_TRAINING
    annee = 2022
    code_unite_enseignement = "ESA2004"


class ActiviteIdentityFactory(factory.Factory):
    class Meta:
        model = ActiviteIdentity
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))


class ActiviteFactory(factory.Factory):
    class Meta:
        model = Activite
        abstract = False

    entity_id = factory.SubFactory(ActiviteIdentityFactory)
    parcours_doctoral_id = factory.SubFactory(_ParcoursDoctoralIdentityFactory)
    categorie = factory.Iterator(CategorieActivite._member_map_.values())
    contexte = ContexteFormation.DOCTORAL_TRAINING
    ects = factory.Faker("pydecimal", left_digits=2, right_digits=1, positive=True)

    @factory.post_generation
    def generate_dto(self, *args, **kwargs):
        module = sys.modules[__name__]
        class_name = f"{self.categorie.name.title().replace('_', '')}DTOFactory"
        self._dto = getattr(module, kwargs.pop('class', class_name))(**kwargs)
