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
from datetime import date
from typing import Dict, List, Optional, Tuple

from django.conf import settings
from django.db.models import Exists, OuterRef, Q, Sum
from django.db.models.functions import Coalesce
from django.utils.translation import get_language

from admission.views import PaginatedList
from parcours_doctoral.ddd.domain.model.enums import (
    BourseRecherche,
    ChoixEtapeParcoursDoctoral,
    ChoixStatutParcoursDoctoral,
)
from parcours_doctoral.ddd.domain.service.i_filtrer_tous_parcours_doctoraux import (
    IListerTousParcoursDoctoraux,
)
from parcours_doctoral.ddd.dtos import ParcoursDoctoralRechercheBODTO
from parcours_doctoral.ddd.dtos.formation import FormationRechercheBODTO
from parcours_doctoral.ddd.formation.domain.model.enums import StatutActivite
from parcours_doctoral.infrastructure.utils import (
    filter_doctorate_queryset_according_to_roles,
    get_entities_with_descendants_ids,
)
from parcours_doctoral.models import Activity, ParcoursDoctoral


class ListerTousParcoursDoctoraux(IListerTousParcoursDoctoraux):
    DATE_FIELD_BY_DATE_TYPE = {
        ChoixEtapeParcoursDoctoral.ADMISSION.name: 'created_at',
        ChoixEtapeParcoursDoctoral.CONFIRMATION.name: 'confirmationpaper__confirmation_date',
    }
    ADDITIONAL_DATE_CONDITION_BY_DATE_TYPE = {
        ChoixEtapeParcoursDoctoral.CONFIRMATION.name: {
            'confirmationpaper__is_active': True,
        }
    }

    @classmethod
    def filtrer(
        cls,
        numero: Optional[int] = None,
        noma: Optional[str] = '',
        matricule_doctorant: Optional[str] = '',
        type_admission: Optional[str] = '',
        statuts: Optional[List[str]] = None,
        annee_academique: Optional[int] = None,
        uuid_promoteur: Optional[str] = '',
        uuid_president_jury: Optional[str] = '',
        cdds: Optional[List[str]] = None,
        commission_proximite: Optional[str] = '',
        type_financement: Optional[str] = '',
        bourse_recherche: Optional[str] = '',
        fnrs_fria_fresh: Optional[bool] = None,
        instituts_secteurs: Optional[List[str]] = None,
        dates: Optional[List[Tuple[str, Optional[date], Optional[date]]]] = None,
        sigles_formations: Optional[List[str]] = None,
        tri_inverse: bool = False,
        champ_tri: Optional[str] = None,
        page: Optional[int] = None,
        taille_page: Optional[int] = None,
        demandeur: Optional[str] = '',
    ) -> PaginatedList[ParcoursDoctoralRechercheBODTO]:
        language_is_french = get_language() == settings.LANGUAGE_CODE_FR

        qs = (
            ParcoursDoctoral.objects.annotate_training_management_entity()
            .annotate_with_reference()
            .annotate(
                scholarship=Coalesce('international_scholarship__short_name', 'other_international_scholarship'),
            )
            .annotate(
                follows_an_additional_training=Exists(
                    Activity.objects.for_complementary_training_filter().filter(parcours_doctoral_id=OuterRef('pk'))
                ),
                validated_credits_number=Sum(
                    'activity__ects',
                    filter=Q(activity__status=StatutActivite.ACCEPTEE.name),
                    default=0,
                ),
            )
            .select_related(
                'admission',
                'student',
                'training__academic_year',
                'training__enrollment_campus',
                'training__education_group_type',
            )
        )

        # Add filters
        if numero:
            qs = qs.filter(reference=numero)

        if noma:
            qs = qs.filter(student__student__registration_id=noma)

        if matricule_doctorant:
            qs = qs.filter(student__global_id=matricule_doctorant)

        if type_admission:
            qs = qs.filter(admission__type=type_admission)

        if sigles_formations:
            qs = qs.filter(training__acronym__in=sigles_formations)

        if statuts:
            qs = qs.filter(status__in=statuts)

        if annee_academique:
            qs = qs.filter(training__academic_year__year=annee_academique)

        if uuid_promoteur:
            qs = qs.filter(supervision_group__actors__uuid=uuid_promoteur)

        if uuid_president_jury:
            qs = qs.filter(jury_members__uuid=uuid_president_jury)

        if demandeur:
            qs = filter_doctorate_queryset_according_to_roles(qs, demandeur)

        if cdds or instituts_secteurs:
            qs = qs.filter(
                training__management_entity_id__in=get_entities_with_descendants_ids(cdds + instituts_secteurs)
            )

        if commission_proximite:
            qs = qs.filter(proximity_commission=commission_proximite)

        if type_financement:
            qs = qs.filter(financing_type=type_financement)

        if bourse_recherche == BourseRecherche.OTHER.name:
            qs = qs.exclude(other_international_scholarship='')
        elif bourse_recherche:
            qs = qs.filter(international_scholarship=bourse_recherche)

        if fnrs_fria_fresh:
            qs = qs.filter(is_fnrs_fria_fresh_csc_linked=fnrs_fria_fresh)

        if dates:
            date_filters: Dict = {}

            for date_type, date_start, date_end in dates:
                date_field = cls.DATE_FIELD_BY_DATE_TYPE[date_type]
                if date_start:
                    date_filters[f'{date_field}__gte'] = date_start
                if date_end:
                    date_filters[f'{date_field}__lte'] = date_end

                additional_condition = cls.ADDITIONAL_DATE_CONDITION_BY_DATE_TYPE.get(date_type)
                if additional_condition:
                    date_filters.update(additional_condition)

            qs = qs.filter(**date_filters)

        field_order = []
        if champ_tri:
            if champ_tri == 'statut':
                qs = qs.annotate_ordered_enum('status', 'ordered_status', ChoixStatutParcoursDoctoral)

            field_order = {
                'reference': ['formatted_reference'],
                'nom_etudiant': ['student__last_name', 'student__first_name'],
                'formation': ['training__acronym'],
                'bourse': ['scholarship'],
                'statut': ['ordered_status'],
                'date_admission': ['created_at'],
                'pre_admission': ['admission__type'],
                'cotutelle': ['cotutelle'],
                'formation_complementaire': ['follows_an_additional_training'],
                'en_regle_inscription': [''],  # TODO
                'total_credits_valides': ['validated_credits_number'],
            }[champ_tri]

            if tri_inverse:
                field_order = ['-' + field for field in field_order]

        qs = qs.order_by(*field_order, 'id')

        # Paginate the queryset
        if page and taille_page:
            result = PaginatedList(complete_list=qs.all().values_list('uuid', flat=True))
            bottom = (page - 1) * taille_page
            top = page * taille_page
            qs = qs[bottom:top]
        else:
            result = PaginatedList(id_attribute='uuid')

        for parcours_doctoral in qs:
            result.append(cls.load_dto_from_model(parcours_doctoral, language_is_french))

        return result

    @classmethod
    def load_dto_from_model(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        language_is_french: bool,
    ) -> ParcoursDoctoralRechercheBODTO:
        return ParcoursDoctoralRechercheBODTO(
            uuid=parcours_doctoral.uuid,
            statut=parcours_doctoral.status,
            reference=parcours_doctoral.formatted_reference,  # From annotation
            matricule_doctorant=parcours_doctoral.student.global_id,
            genre_doctorant=parcours_doctoral.student.gender,
            nom_doctorant=parcours_doctoral.student.last_name,
            prenom_doctorant=parcours_doctoral.student.first_name,
            formation=FormationRechercheBODTO(
                sigle=parcours_doctoral.training.acronym,
                code=parcours_doctoral.training.partial_acronym,
                annee=parcours_doctoral.training.academic_year.year,
                intitule=getattr(parcours_doctoral.training, 'title' if language_is_french else 'title_english'),
                intitule_fr=parcours_doctoral.training.title,
                intitule_en=parcours_doctoral.training.title_english,
                type=parcours_doctoral.training.education_group_type.name,
            ),
            type_admission=parcours_doctoral.admission.type,
            cree_le=parcours_doctoral.created_at,
            code_bourse=parcours_doctoral.scholarship,  # From annotation
            cotutelle=parcours_doctoral.cotutelle,
            formation_complementaire=parcours_doctoral.follows_an_additional_training,
            en_regle_inscription=False,  # TODO
            total_credits_valides=parcours_doctoral.validated_credits_number,
        )
