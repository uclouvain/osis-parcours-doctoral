# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
import itertools
from abc import abstractmethod
from typing import Dict, List

from django.utils.translation import pgettext_lazy

from admission.ddd.admission.doctorat.preparation.read_view.domain.enums.tableau_bord import (
    CategorieTableauBordEnum,
    TypeCategorieTableauBord,
    IndicateurTableauBordEnum,
)
from admission.ddd.admission.doctorat.preparation.read_view.domain.model.tableau_bord import (
    CategorieTableauBord,
    IndicateurTableauBord,
)
from admission.ddd.admission.doctorat.preparation.read_view.repository.i_tableau_bord import (
    ITableauBordRepositoryAdmissionMixin,
)
from osis_common.ddd import interface
from parcours_doctoral.ddd.read_view.dto.tableau_bord import (
    TableauBordDTO,
    CategorieTableauBordDTO,
    IndicateurTableauBordDTO,
)


class ITableauBordRepository(ITableauBordRepositoryAdmissionMixin, interface.ReadModelRepository):
    categories_doctorat: List[CategorieTableauBord] = [
        CategorieTableauBord(
            id=CategorieTableauBordEnum.CONFIRMATION,
            libelle=pgettext_lazy('dashboard-category', 'Confirmation'),
            type=TypeCategorieTableauBord.DOCTORAT,
            indicateurs=[
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.CONFIRMATION_ECHEANCE_2_MOIS,
                    libelle=pgettext_lazy('dashboard-indicator confirmation', 'Deadline 2 months'),
                ),
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.CONFIRMATION_SOUMISE,
                    libelle=pgettext_lazy('dashboard-indicator confirmation', 'Submitted confirmation'),
                ),
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.CONFIRMATION_PV_TELEVERSE,
                    libelle=pgettext_lazy('dashboard-indicator confirmation', 'Submitted PV'),
                ),
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.CONFIRMATION_REPORT_DATE,
                    libelle=pgettext_lazy('dashboard-indicator confirmation', 'Date postponement'),
                ),
            ],
        ),
        CategorieTableauBord(
            id=CategorieTableauBordEnum.FORMATION_DOCTORALE,
            libelle=pgettext_lazy('dashboard-category', 'Doctoral training'),
            type=TypeCategorieTableauBord.DOCTORAT,
            indicateurs=[
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.FORMATION_DOCTORALE_VALIDE_PROMOTEUR,
                    libelle=pgettext_lazy('dashboard-indicator training', 'Validated by promoter'),
                ),
            ],
        ),
        CategorieTableauBord(
            id=CategorieTableauBordEnum.JURY,
            libelle=pgettext_lazy('dashboard-category', 'Jury'),
            type=TypeCategorieTableauBord.DOCTORAT,
            indicateurs=[
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.JURY_VALIDE_CA,
                    libelle=pgettext_lazy('dashboard-indicator jury', 'Validated by CA'),
                ),
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.JURY_REJET_ADRE,
                    libelle=pgettext_lazy('dashboard-indicator jury', 'Rejected by ADRE'),
                ),
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.JURY_VALIDE_ADRE,
                    libelle=pgettext_lazy('dashboard-indicator jury', 'Validated by ADRE'),
                ),
            ],
        ),
        CategorieTableauBord(
            id=CategorieTableauBordEnum.FORMULE_1_DEFENSE_PRIVEE,
            libelle=pgettext_lazy('dashboard-category', 'Private defense (formula 1)'),
            type=TypeCategorieTableauBord.DOCTORAT,
            indicateurs=[
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.FORMULE_1_DEFENSE_PRIVEE_SOUMISE,
                    libelle=pgettext_lazy('dashboard-indicator formula-1-private-defense', 'Submitted private defense'),
                ),
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.FORMULE_1_DEFENSE_PRIVEE_PV_TELEVERSE,
                    libelle=pgettext_lazy('dashboard-indicator formula-1-private-defense', 'Submitted PV'),
                ),
            ],
        ),
        CategorieTableauBord(
            id=CategorieTableauBordEnum.FORMULE_1_SOUTENANCE_PUBLIQUE,
            libelle=pgettext_lazy('dashboard-category', 'Public defense (formula 1)'),
            type=TypeCategorieTableauBord.DOCTORAT,
            indicateurs=[
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.FORMULE_1_SOUTENANCE_PUBLIQUE_SOUMISE,
                    libelle=pgettext_lazy('dashboard-indicator formula-1-public-defense', 'Submitted public defense'),
                ),
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.FORMULE_1_SOUTENANCE_PUBLIQUE_PV_TELEVERSE,
                    libelle=pgettext_lazy('dashboard-indicator formula-1-public-defense', 'Submitted PV'),
                ),
            ],
        ),
        CategorieTableauBord(
            id=CategorieTableauBordEnum.FORMULE_2_RECEVABILITE,
            libelle=pgettext_lazy('dashboard-category', 'Recevability (formula 2)'),
            type=TypeCategorieTableauBord.DOCTORAT,
            indicateurs=[
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.FORMULE_2_RECEVABILITE_SOUMISE,
                    libelle=pgettext_lazy('dashboard-indicator formula-2-admissibility', 'Submitted admissibility'),
                ),
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.FORMULE_2_RECEVABILITE_PV_TELEVERSE,
                    libelle=pgettext_lazy('dashboard-indicator formula-2-admissibility', 'Submitted PV'),
                ),
            ],
        ),
        CategorieTableauBord(
            id=CategorieTableauBordEnum.FORMULE_2_DEFENSE_PRIVEE_SOUTENANCE_PUBLIQUE,
            libelle=pgettext_lazy('dashboard-category', 'Private defense / Public defense (formula 2)'),
            type=TypeCategorieTableauBord.DOCTORAT,
            indicateurs=[
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.FORMULE_2_DEFENSE_PRIVEE_SOUTENANCE_PUBLIQUE_SOUMISE,
                    libelle=pgettext_lazy(
                        'dashboard-indicator formula-2-defense',
                        'Submitted private defense / Submitted public defense',
                    ),
                ),
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.FORMULE_2_DEFENSE_PRIVEE_PV_TELEVERSE,
                    libelle=pgettext_lazy('dashboard-indicator formula-2-defense', 'Submitted PV (private defense)'),
                ),
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.FORMULE_2_SOUTENANCE_PUBLIQUE_PV_TELEVERSE,
                    libelle=pgettext_lazy('dashboard-indicator formula-2-defense', 'Submitted PV (public defense)'),
                ),
            ],
        ),
        CategorieTableauBord(
            id=CategorieTableauBordEnum.AUTORISATION_DIFFUSION_THESE,
            libelle=pgettext_lazy('dashboard-category', 'Thesis distribution authorisation'),
            type=TypeCategorieTableauBord.DOCTORAT,
            indicateurs=[
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.AUTORISATION_DIFFUSION_THESE_ECHEANCE_15_JOURS,
                    libelle=pgettext_lazy('dashboard-indicator thesis-distribution', 'Deadline 15 days'),
                ),
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.AUTORISATION_DIFFUSION_THESE_REJET_ADRE,
                    libelle=pgettext_lazy('dashboard-indicator thesis-distribution', 'Rejected by ADRE'),
                ),
                IndicateurTableauBord(
                    id=IndicateurTableauBordEnum.AUTORISATION_DIFFUSION_THESE_REJET_SCEB,
                    libelle=pgettext_lazy('dashboard-indicator thesis-distribution', 'Rejected by SCEB'),
                ),
            ],
        ),
    ]

    @classmethod
    def get(cls) -> 'TableauBordDTO':
        valeurs = cls._get_valeurs_indicateurs()

        return TableauBordDTO(
            categories={
                category.id.name: CategorieTableauBordDTO(
                    id=category.id.name,
                    type=category.type.name,
                    libelle=category.libelle,
                    indicateurs={
                        indicateur.id.name: IndicateurTableauBordDTO(
                            id=indicateur.id.name,
                            libelle=indicateur.libelle,
                            valeur=valeurs.get(indicateur.id.name, None),
                        )
                        for indicateur in category.indicateurs
                    },
                )
                for category in itertools.chain(cls.categories_admission, cls.categories_doctorat)
            }
        )

    @classmethod
    @abstractmethod
    def _get_valeurs_indicateurs(cls) -> Dict[str, int]:
        raise NotImplementedError
