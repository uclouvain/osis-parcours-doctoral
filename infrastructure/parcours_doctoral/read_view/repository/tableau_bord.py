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
from typing import Dict, List, Optional

from django.db.models.aggregates import Count
from django.db.models.expressions import ExpressionWrapper, F
from django.db.models.fields import DateField
from django.db.models.functions.datetime import Now
from django.db.models.lookups import GreaterThanOrEqual
from django.db.models.query_utils import Q

from admission.ddd.admission.doctorat.preparation.read_view.domain.enums.tableau_bord import (
    IndicateurTableauBordEnum,
)
from admission.infrastructure.admission.doctorat.preparation.read_view.repository.tableau_bord import (
    TableauBordRepositoryAdmissionMixin,
)
from admission.models import DoctorateAdmission
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.read_view.repository.i_tableau_bord import (
    ITableauBordRepository,
)
from parcours_doctoral.infrastructure.utils import get_entities_with_descendants_ids
from parcours_doctoral.models import ParcoursDoctoral


class TableauBordRepository(TableauBordRepositoryAdmissionMixin, ITableauBordRepository):
    DOCTORATE_DJANGO_FILTER_BY_INDICATOR = {
        IndicateurTableauBordEnum.CONFIRMATION_ECHEANCE_2_MOIS.name: Q(
            GreaterThanOrEqual(
                Now(),
                ExpressionWrapper(
                    F('created_at') + (F('confirmationpaper__confirmation_deadline') - F('created_at')) * 0.75,
                    output_field=DateField(),
                ),
            ),
            confirmationpaper__is_active=True,
            status__in=[
                ChoixStatutParcoursDoctoral.ADMIS.name,
                ChoixStatutParcoursDoctoral.CONFIRMATION_A_REPRESENTER.name,
            ],
        ),
        IndicateurTableauBordEnum.CONFIRMATION_SOUMISE.name: Q(
            status=ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name,
        ),
        IndicateurTableauBordEnum.CONFIRMATION_PV_TELEVERSE.name: Q(
            status=ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name,
            confirmationpaper__is_active=True,
            confirmationpaper__supervisor_panel_report__len__gt=0,
        ),
        IndicateurTableauBordEnum.CONFIRMATION_REPORT_DATE.name: Q(
            status__in=[
                ChoixStatutParcoursDoctoral.ADMIS.name,
            ],
            confirmationpaper__is_active=True,
            confirmationpaper__extended_deadline__isnull=False,
        ),
        # IndicateurTableauBordEnum.FORMATION_DOCTORALE_VALIDE_PROMOTEUR.name: Q(),
        IndicateurTableauBordEnum.JURY_VALIDE_CA.name: Q(
            status=ChoixStatutParcoursDoctoral.JURY_APPROUVE_CA.name,
        ),
        IndicateurTableauBordEnum.JURY_REJET_ADRE.name: Q(
            status=ChoixStatutParcoursDoctoral.JURY_REFUSE_ADRE.name,
        ),
        IndicateurTableauBordEnum.JURY_VALIDE_ADRE.name: Q(
            status=ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE.name,
        ),
        # IndicateurTableauBordEnum.RECEVABILITE_SOUMISE.name: Q(),
        # IndicateurTableauBordEnum.RECEVABILITE_PV_TELEVERSE.name: Q(),
        IndicateurTableauBordEnum.FORMULE_1_DEFENSE_PRIVEE_SOUMISE.name: Q(
            status=ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE.name,
        ),
        IndicateurTableauBordEnum.FORMULE_1_DEFENSE_PRIVEE_PV_TELEVERSE.name: Q(
            status=ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE.name,
            current_private_defense__minutes__len__gt=0,
        ),
        IndicateurTableauBordEnum.FORMULE_1_SOUTENANCE_PUBLIQUE_SOUMISE.name: Q(
            status=ChoixStatutParcoursDoctoral.SOUTENANCE_PUBLIQUE_SOUMISE.name,
        ),
        # IndicateurTableauBordEnum.AUTORISATION_DIFFUSION_THESE_ECHEANCE_15_JOURS.name: Q(),
        # IndicateurTableauBordEnum.AUTORISATION_DIFFUSION_THESE_REJET_ADRE.name: Q(),
        # IndicateurTableauBordEnum.AUTORISATION_DIFFUSION_THESE_REJET_SCEB.name: Q(),
        # IndicateurTableauBordEnum.SOUTENANCE_PUBLIQUE_PV_TELEVERSE.name: Q(),
    }

    @classmethod
    def _get_valeurs_indicateurs(
        cls,
        commission_proximite: Optional[str],
        cdds: Optional[List[str]],
    ) -> Dict[str, int]:
        common_filters = Q()
        if commission_proximite:
            common_filters &= Q(proximity_commission=commission_proximite)

        if cdds:
            common_filters &= Q(training__management_entity_id__in=get_entities_with_descendants_ids(cdds))

        doctorate_results = ParcoursDoctoral.objects.aggregate(
            **{
                indicator: Count('pk', filter=django_filter & common_filters)
                for indicator, django_filter in cls.DOCTORATE_DJANGO_FILTER_BY_INDICATOR.items()
            }
        )

        admission_results = DoctorateAdmission.objects.aggregate(
            **{
                indicator: Count('pk', filter=django_filter & common_filters)
                for indicator, django_filter in cls.ADMISSION_DJANGO_FILTER_BY_INDICATOR.items()
            }
        )

        return {
            **doctorate_results,
            **admission_results,
        }
