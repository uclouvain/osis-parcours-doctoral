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
from typing import List

from parcours_doctoral.ddd.builder.parcours_doctoral_identity import (
    ParcoursDoctoralIdentityBuilder,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.epreuve_confirmation.builder.epreuve_confirmation_identity import (
    EpreuveConfirmationIdentityBuilder,
)
from parcours_doctoral.ddd.epreuve_confirmation.domain.model._demande_prolongation import (
    DemandeProlongation,
)
from parcours_doctoral.ddd.epreuve_confirmation.domain.model.epreuve_confirmation import (
    EpreuveConfirmation,
    EpreuveConfirmationIdentity,
)
from parcours_doctoral.ddd.epreuve_confirmation.dtos import (
    DemandeProlongationDTO,
    EpreuveConfirmationDTO,
)
from parcours_doctoral.ddd.epreuve_confirmation.repository.i_epreuve_confirmation import (
    IEpreuveConfirmationRepository,
)
from parcours_doctoral.ddd.epreuve_confirmation.validators.exceptions import (
    EpreuveConfirmationNonTrouveeException,
)
from parcours_doctoral.models import ParcoursDoctoral
from parcours_doctoral.models.confirmation_paper import ConfirmationPaper


class EpreuveConfirmationRepository(IEpreuveConfirmationRepository):
    @classmethod
    def get_dto(cls, entity_id: 'EpreuveConfirmationIdentity') -> 'EpreuveConfirmationDTO':
        try:
            confirmation_paper = ConfirmationPaper.objects.get(uuid=entity_id.uuid)
        except ConfirmationPaper.DoesNotExist:
            raise EpreuveConfirmationNonTrouveeException

        return cls._load_confirmation_dto(confirmation_paper)

    @classmethod
    def search_by_parcours_doctoral_identity(
        cls, parcours_doctoral_entity_id: 'ParcoursDoctoralIdentity'
    ) -> List['EpreuveConfirmation']:
        confirmation_papers = ConfirmationPaper.objects.filter(parcours_doctoral__uuid=parcours_doctoral_entity_id.uuid)
        return [
            cls._load_confirmation(parcours_doctoral_entity_id, confirmation_paper)
            for confirmation_paper in confirmation_papers
        ]

    @classmethod
    def search_dto_by_parcours_doctoral_identity(
        cls, parcours_doctoral_entity_id: 'ParcoursDoctoralIdentity'
    ) -> List['EpreuveConfirmationDTO']:
        confirmation_papers = ConfirmationPaper.objects.filter(parcours_doctoral__uuid=parcours_doctoral_entity_id.uuid)
        return [cls._load_confirmation_dto(confirmation_paper) for confirmation_paper in confirmation_papers]

    @classmethod
    def get_last_dto_by_parcours_doctoral_identity(
        cls, parcours_doctoral_entity_id: 'ParcoursDoctoralIdentity'
    ) -> 'EpreuveConfirmationDTO':
        first_result = ConfirmationPaper.objects.filter(
            parcours_doctoral__uuid=parcours_doctoral_entity_id.uuid,
            is_active=True,
        ).first()
        if not first_result:
            raise EpreuveConfirmationNonTrouveeException
        return cls._load_confirmation_dto(first_result)

    @classmethod
    def save(cls, entity: 'EpreuveConfirmation') -> 'EpreuveConfirmationIdentity':
        related_parcours_doctoral = ParcoursDoctoral.objects.get(uuid=entity.parcours_doctoral_id.uuid)

        extended_deadline_params = (
            {
                'extended_deadline': entity.demande_prolongation.nouvelle_echeance,
                'cdd_opinion': entity.demande_prolongation.avis_cdd,
                'justification_letter': entity.demande_prolongation.lettre_justification,
                'brief_justification': entity.demande_prolongation.justification_succincte,
            }
            if entity.demande_prolongation
            else {}
        )

        ConfirmationPaper.objects.update_or_create(
            uuid=entity.entity_id.uuid,
            defaults={
                'parcours_doctoral': related_parcours_doctoral,
                'confirmation_date': entity.date,
                'confirmation_deadline': entity.date_limite,
                'research_report': entity.rapport_recherche,
                'supervisor_panel_report': entity.proces_verbal_ca,
                'supervisor_panel_report_canvas': entity.canevas_proces_verbal_ca,
                'research_mandate_renewal_opinion': entity.avis_renouvellement_mandat_recherche,
                'certificate_of_failure': entity.attestation_echec,
                'certificate_of_achievement': entity.attestation_reussite,
                'is_active': entity.est_active,
                **extended_deadline_params,
            },
        )

        return entity.entity_id

    @classmethod
    def get(cls, entity_id: 'EpreuveConfirmationIdentity') -> 'EpreuveConfirmation':
        try:
            confirmation_paper = ConfirmationPaper.objects.select_related('parcours_doctoral').get(uuid=entity_id.uuid)
        except ConfirmationPaper.DoesNotExist:
            raise EpreuveConfirmationNonTrouveeException

        return cls._load_confirmation(
            entity_id=ParcoursDoctoralIdentityBuilder.build_from_uuid(confirmation_paper.parcours_doctoral.uuid),
            confirmation_paper=confirmation_paper,
        )

    @classmethod
    def _load_confirmation_dto(cls, confirmation_paper: ConfirmationPaper) -> EpreuveConfirmationDTO:
        return EpreuveConfirmationDTO(
            uuid=str(confirmation_paper.uuid),
            est_active=confirmation_paper.is_active,
            date_limite=confirmation_paper.confirmation_deadline,
            date=confirmation_paper.confirmation_date,
            rapport_recherche=confirmation_paper.research_report,
            demande_prolongation=(
                DemandeProlongationDTO(
                    nouvelle_echeance=confirmation_paper.extended_deadline,
                    justification_succincte=confirmation_paper.brief_justification,
                    lettre_justification=confirmation_paper.justification_letter,
                    avis_cdd=confirmation_paper.cdd_opinion,
                )
                if confirmation_paper.extended_deadline
                else None
            ),
            proces_verbal_ca=confirmation_paper.supervisor_panel_report,
            attestation_reussite=confirmation_paper.certificate_of_achievement,
            attestation_echec=confirmation_paper.certificate_of_failure,
            canevas_proces_verbal_ca=confirmation_paper.supervisor_panel_report_canvas,
            avis_renouvellement_mandat_recherche=confirmation_paper.research_mandate_renewal_opinion,
        )

    @classmethod
    def _load_confirmation(
        cls,
        entity_id: 'ParcoursDoctoralIdentity',
        confirmation_paper: ConfirmationPaper,
    ) -> EpreuveConfirmation:
        return EpreuveConfirmation(
            entity_id=EpreuveConfirmationIdentityBuilder.build_from_uuid(str(confirmation_paper.uuid)),
            parcours_doctoral_id=entity_id,
            date_limite=confirmation_paper.confirmation_deadline,
            date=confirmation_paper.confirmation_date,
            rapport_recherche=confirmation_paper.research_report,
            demande_prolongation=(
                DemandeProlongation(
                    nouvelle_echeance=confirmation_paper.extended_deadline,
                    justification_succincte=confirmation_paper.brief_justification,
                    lettre_justification=confirmation_paper.justification_letter,
                    avis_cdd=confirmation_paper.cdd_opinion,
                )
                if confirmation_paper.extended_deadline
                else None
            ),
            proces_verbal_ca=confirmation_paper.supervisor_panel_report,
            attestation_reussite=confirmation_paper.certificate_of_achievement,
            attestation_echec=confirmation_paper.certificate_of_failure,
            canevas_proces_verbal_ca=confirmation_paper.supervisor_panel_report_canvas,
            avis_renouvellement_mandat_recherche=confirmation_paper.research_mandate_renewal_opinion,
            est_active=confirmation_paper.is_active,
        )
