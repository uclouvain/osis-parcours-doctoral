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
from typing import List, Optional, Tuple, Dict

from django.db.models.functions import Coalesce

from admission.ddd.admission.doctorat.preparation.domain.model.enums import BourseRecherche, \
    ChoixStatutPropositionDoctorale
from admission.views import PaginatedList
from django.conf import settings
from django.db.models import Q
from django.utils.translation import get_language

from parcours_doctoral.ddd.domain.model.enums import ChoixEtapeParcoursDoctoral
from parcours_doctoral.ddd.domain.service.i_filtrer_tous_parcours_doctoraux import (
    IListerTousParcoursDoctoraux,
)
from parcours_doctoral.ddd.dtos import (
    CampusDTO,
    EntiteGestionDTO,
    FormationDTO,
    ParcoursDoctoralRechercheDTO,
)
from parcours_doctoral.ddd.jury.domain.model.enums import RoleJury
from parcours_doctoral.infrastructure.utils import get_entities_with_descendants_ids
from parcours_doctoral.models import ParcoursDoctoral


class ListerTousParcoursDoctoraux(IListerTousParcoursDoctoraux):
    DATE_FIELD_BY_DATE_TYPE = {
        ChoixEtapeParcoursDoctoral.ADMISSION.name: 'created_at',
        ChoixEtapeParcoursDoctoral.CONFIRMATION.name: 'confirmationpaper__confirmation_date',
    }

    @classmethod
    def filtrer(
        cls,
        numero: Optional[int] = None,
        noma: Optional[str] = '',
        matricule_etudiant: Optional[str] = '',
        statuts: Optional[List[str]] = None,
        formation: Optional[str] = '',
        annee_academique: Optional[int] = None,
        matricule_promoteur: Optional[str] = '',
        matricule_president_jury: Optional[str] = '',
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
    ) -> PaginatedList[ParcoursDoctoralRechercheDTO]:
        language_is_french = get_language() == settings.LANGUAGE_CODE_FR

        qs = (
            ParcoursDoctoral.objects.annotate_training_management_entity()
            .annotate_with_reference()
            .annotate_campus_info()
            .annotate(
                scholarship=Coalesce('international_scholarship__short_name', 'other_international_scholarship'),
            )
            .select_related(
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

        if matricule_etudiant:
            qs = qs.filter(student__global_id=matricule_etudiant)

        if formation:
            terms = formation.split()
            training_filters = Q()
            for term in terms:
                # The term can be a part of the acronym or of the training title
                training_filters &= Q(Q(training__acronym__icontains=term) | Q(training__title__icontains=term))
            qs = qs.filter(training_filters)

        if sigles_formations:
            qs = qs.filter(training__acronym__in=sigles_formations)

        if statuts:
            qs = qs.filter(status__in=statuts)

        if annee_academique:
            qs = qs.filter(training__academic_year__year=annee_academique)

        if matricule_promoteur:
            qs = qs.filter(supervision_group__actors__person__global_id=matricule_promoteur)

        if matricule_president_jury:
            qs = qs.filter(
                jury_members__role=RoleJury.PRESIDENT.name,
                jury_members__person__global_id=matricule_president_jury,
            )

        if cdds or instituts_secteurs:
            related_entities = get_entities_with_descendants_ids(cdds + instituts_secteurs)
            qs = qs.filter(training__management_entity_id__in=related_entities)

        if commission_proximite:
            qs = qs.filter(proximity_commission=commission_proximite)

        if type_financement:
            qs = qs.filter(financing_type=type_financement)

        if bourse_recherche == BourseRecherche.OTHER.name:
            qs = qs.exclude(other_international_scholarship='')
        elif bourse_recherche:
            qs = qs.filter(international_scholarship=bourse_recherche)

        if fnrs_fria_fresh is not None:
            qs = qs.filter(is_fnrs_fria_fresh_csc_linked=fnrs_fria_fresh)

        if dates:
            date_filters: Dict = {}
            for date_type, date_start, date_end in dates:
                date_field = cls.DATE_FIELD_BY_DATE_TYPE[date_type]
                if date_start:
                    date_filters[f'{date_field}__gte'] = date_start
                if date_end:
                    date_filters[f'{date_field}__lte'] = date_end

            qs = qs.filter(**date_filters)

        field_order = []
        if champ_tri:
            if champ_tri == 'statut':
                qs = qs.annotate_ordered_enum('status', 'ordered_status', ChoixStatutPropositionDoctorale)

            field_order = {
                'reference': ['formatted_reference'],
                'nom_etudiant': ['student__last_name', 'student__first_name'],
                'formation': ['training__acronym'],
                'bourse': ['scholarship'],
                'statut': ['ordered_status'],
                'date_admission': ['created_at'],
                'pre_admission': [''], # TODO
                'cotutelle': ['cotutelle'],
                'formation_complementaire': [''], # TODO
                'en_regle_inscription': [''], # TODO
                'total_credits_valides': [''], # TODO
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
    ) -> ParcoursDoctoralRechercheDTO:
        return ParcoursDoctoralRechercheDTO(
            uuid=parcours_doctoral.uuid,
            statut=parcours_doctoral.status,
            reference=parcours_doctoral.formatted_reference,  # From annotation
            matricule_doctorant=parcours_doctoral.student.global_id,
            genre_doctorant=parcours_doctoral.student.gender,
            nom_doctorant=parcours_doctoral.student.last_name,
            prenom_doctorant=parcours_doctoral.student.first_name,
            formation=FormationDTO(
                sigle=parcours_doctoral.training.acronym,
                code=parcours_doctoral.training.partial_acronym,
                annee=parcours_doctoral.training.academic_year.year,
                intitule=getattr(parcours_doctoral.training, 'title' if language_is_french else 'title_english'),
                intitule_fr=parcours_doctoral.training.title,
                intitule_en=parcours_doctoral.training.title_english,
                type=parcours_doctoral.training.education_group_type.name,
                campus=CampusDTO(
                    uuid=parcours_doctoral.teaching_campus_info['uuid'],
                    nom=parcours_doctoral.teaching_campus_info['name'],
                    code_postal=parcours_doctoral.teaching_campus_info['postal_code'],
                    ville=parcours_doctoral.teaching_campus_info['city'],
                    pays_iso_code=parcours_doctoral.teaching_campus_info['country_code'],
                    nom_pays=(
                        parcours_doctoral.teaching_campus_info['fr_country_name']
                        if language_is_french
                        else parcours_doctoral.teaching_campus_info['en_country_name']
                    ),
                    rue=parcours_doctoral.teaching_campus_info['street'],
                    numero_rue=parcours_doctoral.teaching_campus_info['street_number'],
                    boite_postale=parcours_doctoral.teaching_campus_info['postal_box'],
                    localisation=parcours_doctoral.teaching_campus_info['location'],
                ),  # From annotation
                # TODO
                entite_gestion=EntiteGestionDTO(),
            ),
            cree_le=parcours_doctoral.created_at,
            code_bourse=parcours_doctoral.scholarship,  # From annotation
            cotutelle=parcours_doctoral.cotutelle,
            formation_complementaire=False,  # TODO
            en_regle_inscription=False,  # TODO
            total_credits_valides=0,  # TODO
        )
