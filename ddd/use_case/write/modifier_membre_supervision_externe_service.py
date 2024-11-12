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
from parcours_doctoral.ddd.commands import ModifierMembreSupervisionExterneCommand
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoralIdentity
from parcours_doctoral.ddd.domain.service.i_membre_CA import IMembreCATranslator
from parcours_doctoral.ddd.domain.service.i_promoteur import IPromoteurTranslator
from parcours_doctoral.ddd.domain.service.membres_groupe_de_supervision import (
    MembresGroupeDeSupervision,
)
from parcours_doctoral.ddd.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from parcours_doctoral.ddd.repository.i_parcours_doctoral import IParcoursDoctoralRepository


def modifier_membre_supervision_externe(
    cmd: 'ModifierMembreSupervisionExterneCommand',
    proposition_repository: 'IParcoursDoctoralRepository',
    groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
    promoteur_translator: 'IPromoteurTranslator',
    membre_ca_translator: 'IMembreCATranslator',
    historique: 'IHistorique',
) -> 'ParcoursDoctoralIdentity':
    # GIVEN
    proposition_id = ParcoursDoctoralIdentityBuilder.build_from_command(cmd)
    proposition = proposition_repository.get(proposition_id)
    groupe_de_supervision = groupe_supervision_repository.get_by_parcours_doctoral_id(proposition_id)
    signataire = groupe_de_supervision.get_signataire(cmd.uuid_membre)

    # WHEN
    groupe_de_supervision.verifier_signatures_non_envoyees()
    MembresGroupeDeSupervision.verifier_externe(
        signataire,
        promoteur_translator,
        membre_ca_translator,
    )

    # THEN
    groupe_supervision_repository.edit_external_member(
        groupe_id=groupe_de_supervision.entity_id,
        membre_id=signataire,
        first_name=cmd.prenom,
        last_name=cmd.nom,
        email=cmd.email,
        is_doctor=cmd.est_docteur,
        institute=cmd.institution,
        city=cmd.ville,
        country_code=cmd.pays,
        language=cmd.langue,
    )
    historique.historiser_modification_membre(proposition, signataire, cmd.matricule_auteur)

    return proposition_id
