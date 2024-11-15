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
from parcours_doctoral.ddd.builder.parcours_doctoral_identity import ParcoursDoctoralIdentityBuilder
from parcours_doctoral.ddd.commands import IdentifierMembreCACommand
from parcours_doctoral.ddd.domain.model._membre_CA import MembreCAIdentity
from parcours_doctoral.ddd.domain.service.i_historique import IHistorique
from parcours_doctoral.ddd.domain.service.i_membre_CA import IMembreCATranslator
from parcours_doctoral.ddd.domain.service.membres_groupe_de_supervision import (
    MembresGroupeDeSupervision,
)
from parcours_doctoral.ddd.domain.validator.validator_by_business_action import (
    IdentifierMembreCAValidatorList,
)
from parcours_doctoral.ddd.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from parcours_doctoral.ddd.repository.i_parcours_doctoral import IParcoursDoctoralRepository
from parcours_doctoral.models import ActorType


def identifier_membre_ca(
    cmd: 'IdentifierMembreCACommand',
    parcours_doctoral_repository: 'IParcoursDoctoralRepository',
    groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
    membre_ca_translator: 'IMembreCATranslator',
    historique: 'IHistorique',
) -> 'MembreCAIdentity':
    # GIVEN
    parcours_doctoral_id = ParcoursDoctoralIdentityBuilder.build_from_uuid(cmd.uuid_parcours_doctoral)
    groupe_de_supervision = groupe_supervision_repository.get_by_parcours_doctoral_id(parcours_doctoral_id)
    parcours_doctoral = parcours_doctoral_repository.get(parcours_doctoral_id)

    # WHEN
    membre_ca_translator.verifier_existence(matricule=cmd.matricule)
    IdentifierMembreCAValidatorList(
        groupe_de_supervision=groupe_de_supervision,
        matricule=cmd.matricule,
        prenom=cmd.prenom,
        nom=cmd.nom,
        email=cmd.email,
        institution=cmd.institution,
        ville=cmd.ville,
        pays=cmd.pays,
        langue=cmd.langue,
    ).validate()
    MembresGroupeDeSupervision.verifier_pas_deja_present(
        groupe_de_supervision.entity_id,
        groupe_supervision_repository,
        matricule=cmd.matricule,
        email=cmd.email,
    )

    # THEN
    membre_ca_id = groupe_supervision_repository.add_member(
        groupe_id=groupe_de_supervision.entity_id,
        matricule=cmd.matricule,
        type=ActorType.CA_MEMBER,
        first_name=cmd.prenom,
        last_name=cmd.nom,
        email=cmd.email,
        is_doctor=cmd.est_docteur,
        institute=cmd.institution,
        city=cmd.ville,
        country_code=cmd.pays,
        language=cmd.langue,
    )
    historique.historiser_ajout_membre(parcours_doctoral, groupe_de_supervision, membre_ca_id, cmd.matricule_auteur)

    return membre_ca_id  # type: ignore[return-value]
