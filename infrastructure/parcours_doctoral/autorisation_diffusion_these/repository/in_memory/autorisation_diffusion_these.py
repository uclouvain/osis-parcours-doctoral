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
import datetime
from typing import List

from base.ddd.utils.in_memory_repository import InMemoryGenericRepository
from parcours_doctoral.constants import INSTITUTION_UCL
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.autorisation_diffusion_these import (
    AutorisationDiffusionThese,
    AutorisationDiffusionTheseIdentity,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.validator.exceptions import (
    AutorisationDiffusionTheseNonTrouveException,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.dtos.autorisation_diffusion_these import (
    AutorisationDiffusionTheseDTO,
    SignataireAutorisationDiffusionTheseDTO,
    SignatureAutorisationDiffusionTheseDTO,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.repository.i_autorisation_diffusion_these import (
    IAutorisationDiffusionTheseRepository,
)


class AutorisationDiffusionTheseInMemoryRepository(InMemoryGenericRepository, IAutorisationDiffusionTheseRepository):
    entities: List[AutorisationDiffusionThese]

    @classmethod
    def get(cls, entity_id: 'AutorisationDiffusionTheseIdentity') -> 'AutorisationDiffusionThese':
        entity = super().get(entity_id=entity_id)

        if not entity:
            raise AutorisationDiffusionTheseNonTrouveException

        return entity

    @classmethod
    def get_dto(cls, entity_id: 'AutorisationDiffusionTheseIdentity') -> 'AutorisationDiffusionTheseDTO':
        entity = cls.get(entity_id=entity_id)

        return AutorisationDiffusionTheseDTO(
            uuid=str(entity.entity_id.uuid),
            statut=entity.statut.name,
            sources_financement=entity.sources_financement,
            resume_anglais=entity.resume_anglais,
            resume_autre_langue=entity.resume_autre_langue,
            mots_cles=entity.mots_cles,
            type_modalites_diffusion=entity.type_modalites_diffusion.name if entity.type_modalites_diffusion else '',
            date_embargo=entity.date_embargo,
            limitations_additionnelles_chapitres=entity.limitations_additionnelles_chapitres,
            modalites_diffusion_acceptees_le=entity.modalites_diffusion_acceptees_le,
            signataires=[
                SignataireAutorisationDiffusionTheseDTO(
                    uuid='',
                    matricule=signataire.entity_id.matricule,
                    role=signataire.entity_id.role.name,
                    nom='',
                    prenom='',
                    email='',
                    genre='',
                    institution=INSTITUTION_UCL,
                    signature=SignatureAutorisationDiffusionTheseDTO(
                        etat=signataire.signature.etat.name,
                        date_heure=datetime.datetime(2025, 1, 1),
                        commentaire_externe=signataire.signature.commentaire_externe,
                        commentaire_interne=signataire.signature.commentaire_interne,
                        motif_refus=signataire.signature.motif_refus,
                    ),
                )
                for signataire in entity.signataires.values()
            ],
        )

    @classmethod
    def save(cls, entity: 'AutorisationDiffusionThese') -> 'AutorisationDiffusionTheseIdentity':
        return super().save(entity=entity)
