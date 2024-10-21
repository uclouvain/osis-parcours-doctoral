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
import datetime
from typing import List, Optional

from admission.views import PaginatedList
from django.conf import settings
from django.db.models import Q
from django.utils.translation import get_language

from parcours_doctoral.ddd.domain.service.i_filtrer_tous_parcours_doctoraux import (
    IListerTousParcoursDoctoraux,
)
from parcours_doctoral.ddd.dtos import (
    CampusDTO,
    EntiteGestionDTO,
    FormationDTO,
    ParcoursDoctoralRechercheDTO,
)
from parcours_doctoral.models import ParcoursDoctoral


class ListerTousParcoursDoctoraux(IListerTousParcoursDoctoraux):
    @classmethod
    def filtrer(
        cls,
        numero: Optional[int] = None,
        noma: Optional[str] = '',
        matricule_etudiant: Optional[str] = '',
        etats: Optional[List[str]] = None,
        formation: Optional[str] = '',
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
                if term.endswith('-1'):
                    training_filters &= Q(est_premiere_annee=True)
                    term = term[:-2]
                # The term can be a part of the acronym or of the training title
                training_filters &= Q(Q(training__acronym__icontains=term) | Q(training__title__icontains=term))
            qs = qs.filter(training_filters)
        if etats:
            qs = qs.filter(status__in=etats)

        field_order = []
        if champ_tri:
            field_order = {
                'reference': ['formatted_reference'],
                'nom_etudiant': ['student__last_name', 'student__first_name'],
                'formation': ['training__acronym'],
                'statut': ['status'],
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
        cls, parcours_doctoral: ParcoursDoctoral, language_is_french: bool
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
        )
