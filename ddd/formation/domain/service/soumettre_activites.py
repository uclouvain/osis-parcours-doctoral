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
from functools import partial
from typing import List

from base.ddd.utils.business_validator import execute_functions_and_aggregate_exceptions
from osis_common.ddd import interface

from parcours_doctoral.ddd.formation.builder.activite_identity_builder import (
    ActiviteIdentityBuilder,
)
from parcours_doctoral.ddd.formation.domain.model.activite import (
    Activite,
    ActiviteIdentity,
)
from parcours_doctoral.ddd.formation.domain.model.enums import (
    CategorieActivite,
    StatutActivite,
)
from parcours_doctoral.ddd.formation.domain.validator.exceptions import (
    ActiviteDoitEtreNonSoumise,
)
from parcours_doctoral.ddd.formation.domain.validator.validator_by_business_action import *
from parcours_doctoral.ddd.formation.dtos import *
from parcours_doctoral.ddd.formation.repository.i_activite import IActiviteRepository


class SoumettreActivites(interface.DomainService):
    @classmethod
    def verifier(cls, activite_uuids: List[str], activite_repository: IActiviteRepository) -> List[Activite]:
        entity_ids = [ActiviteIdentityBuilder.build_from_uuid(uuid) for uuid in activite_uuids]
        dtos = activite_repository.get_dtos(entity_ids)
        activites = activite_repository.get_multiple(entity_ids)
        execute_functions_and_aggregate_exceptions(
            *[
                partial(
                    cls.verifier_activite,
                    activite=activites[entity_id],
                    dto=dtos[entity_id],
                    activite_repository=activite_repository,
                )
                for entity_id in entity_ids
            ],
            *[partial(cls.verifier_statut, activite=activites[entity_id]) for entity_id in entity_ids],
        )
        return list(activites.values())

    @classmethod
    def verifier_statut(cls, activite: Activite) -> None:
        if activite.statut != StatutActivite.NON_SOUMISE:
            raise ActiviteDoitEtreNonSoumise(activite.entity_id)

    @classmethod
    def verifier_activite(cls, activite: Activite, dto: ActiviteDTO, activite_repository: IActiviteRepository) -> None:
        if isinstance(dto, ConferenceDTO):
            ConferenceValidatorList(conference=dto, activite=activite).validate()
        elif isinstance(dto, ConferenceCommunicationDTO):
            ConferenceCommunicationValidatorList(communication=dto, activite=activite).validate()
        elif isinstance(dto, ConferencePublicationDTO):
            ConferencePublicationValidatorList(publication=dto, activite=activite).validate()
        elif isinstance(dto, CommunicationDTO):
            CommunicationValidatorList(communication=dto, activite=activite).validate()
        elif isinstance(dto, PublicationDTO):
            PublicationValidatorList(publication=dto, activite=activite).validate()
        elif isinstance(dto, SejourDTO):
            SejourValidatorList(sejour=dto, activite=activite).validate()
        elif isinstance(dto, SejourCommunicationDTO):
            SejourCommunicationValidatorList(communication=dto, activite=activite).validate()
        elif isinstance(dto, SeminaireDTO):
            SeminaireValidatorList(seminaire=dto, activite=activite).validate()
            # Also check children
            for sous_activite in activite_repository.search(parent_id=activite.entity_id):
                sous_dto = activite_repository.get_dto(sous_activite.entity_id)
                cls.verifier_activite(sous_activite, sous_dto, activite_repository)
        elif isinstance(dto, SeminaireCommunicationDTO):
            SeminaireCommunicationValidatorList(communication=dto, activite=activite).validate()
        elif isinstance(dto, ServiceDTO):
            ServiceValidatorList(service=dto, activite=activite).validate()
        elif isinstance(dto, ValorisationDTO):
            ValorisationValidatorList(valorisation=dto, activite=activite).validate()
        elif isinstance(dto, CoursDTO):
            CoursValidatorList(cours=dto, activite=activite).validate()
        elif isinstance(dto, EpreuveDTO):  # pragma: no branch
            EpreuveValidatorList(epreuve=dto, activite=activite).validate()

    @classmethod
    def soumettre(cls, activites: List[Activite], activite_repository: IActiviteRepository) -> List[ActiviteIdentity]:
        for activite in activites:
            activite.soumettre()
            # TODO Performance ?
            activite_repository.save(activite)
            # Also submit sub-activities for seminars
            if activite.categorie == CategorieActivite.SEMINAR:
                for sous_activite in activite_repository.search(parent_id=activite.entity_id):
                    sous_activite.soumettre()
                    activite_repository.save(sous_activite)
        return [activite.entity_id for activite in activites]
