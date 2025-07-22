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
from uuid import uuid4

from deliberation.models.enums.numero_session import Session
from osis_common.ddd.interface import EntityIdentityBuilder, RootEntityBuilder
from parcours_doctoral.ddd.formation.builder.activite_identity_builder import (
    ActiviteIdentityBuilder,
)
from parcours_doctoral.ddd.formation.commands import InscrireEvaluationCommand
from parcours_doctoral.ddd.formation.domain.model.enums import (
    StatutInscriptionEvaluation,
)
from parcours_doctoral.ddd.formation.domain.model.inscription_evaluation import (
    InscriptionEvaluation,
    InscriptionEvaluationIdentity,
)
from parcours_doctoral.ddd.formation.dtos.evaluation import EvaluationDTO
from parcours_doctoral.ddd.formation.dtos.inscription_evaluation import (
    InscriptionEvaluationDTO,
)


class InscriptionEvaluationIdentityBuilder(EntityIdentityBuilder):
    @classmethod
    def build_from_uuid(cls, uuid: str) -> InscriptionEvaluationIdentity:
        return InscriptionEvaluationIdentity(uuid=uuid)


class InscriptionEvaluationBuilder(RootEntityBuilder):
    @classmethod
    def build_from_command(cls, cmd: 'InscrireEvaluationCommand') -> 'InscriptionEvaluation':
        return InscriptionEvaluation(
            entity_id=InscriptionEvaluationIdentityBuilder.build_from_uuid(uuid=str(uuid4())),
            cours_id=ActiviteIdentityBuilder.build_from_uuid(uuid=cmd.cours_uuid),
            session=Session[cmd.session],
            inscription_tardive=cmd.inscription_tardive,
            statut=StatutInscriptionEvaluation.ACCEPTEE,
            desinscription_tardive=False,
        )

    @classmethod
    def build_from_repository_dto(cls, dto_object: 'InscriptionEvaluationDTO') -> 'InscriptionEvaluation':
        return InscriptionEvaluation(
            entity_id=InscriptionEvaluationIdentityBuilder.build_from_uuid(uuid=dto_object.uuid),
            cours_id=ActiviteIdentityBuilder.build_from_uuid(uuid=dto_object.uuid_activite),
            session=Session[dto_object.session],
            inscription_tardive=dto_object.inscription_tardive,
            statut=StatutInscriptionEvaluation[dto_object.statut],
            desinscription_tardive=dto_object.desinscription_tardive,
        )

    @classmethod
    def build_from_evaluation_dto(cls, dto_object: 'EvaluationDTO') -> 'InscriptionEvaluation':
        return InscriptionEvaluation(
            entity_id=InscriptionEvaluationIdentityBuilder.build_from_uuid(uuid=dto_object.uuid),
            cours_id=ActiviteIdentityBuilder.build_from_uuid(uuid=dto_object.uuid_activite),
            session=Session[Session.get_key_session(dto_object.session)],
            inscription_tardive=dto_object.est_inscrit_tardivement,
            statut=StatutInscriptionEvaluation[dto_object.statut],
            desinscription_tardive=dto_object.est_desinscrit_tardivement,
        )
