# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List, Optional

from django.conf import settings
from django.utils.translation import get_language

from admission.contrib.models.doctorate import DoctorateAdmission
from admission.ddd.admission.domain.model.bourse import BourseIdentity
from parcours_doctoral.ddd.domain.validator.exceptions import ParcoursDoctoralNonTrouveException
from parcours_doctoral.models.parcours_doctoral import ParcoursDoctoral as ParcoursDoctoralModel
from parcours_doctoral.ddd.domain.model._formation import FormationIdentity
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoral, ParcoursDoctoralIdentity
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.dtos import ParcoursDoctoralDTO
from parcours_doctoral.ddd.repository.i_doctorat import IParcoursDoctoralRepository
from admission.infrastructure.admission.domain.service.bourse import BourseTranslator
from base.models.student import Student
from osis_common.ddd.interface import ApplicationService, EntityIdentity, RootEntity


class ParcoursDoctoralRepository(IParcoursDoctoralRepository):
    @classmethod
    def delete(cls, entity_id: EntityIdentity, **kwargs: ApplicationService) -> None:
        raise NotImplementedError

    @classmethod
    def search(cls, entity_ids: Optional[List[EntityIdentity]] = None, **kwargs) -> List[RootEntity]:
        raise NotImplementedError

    @classmethod
    def get(cls, entity_id: 'ParcoursDoctoralIdentity') -> 'ParcoursDoctoral':
        try:
            doctorate: ParcoursDoctoral = ParcoursDoctoralModel.objects.get(uuid=entity_id.uuid)
        except ParcoursDoctoral.DoesNotExist:
            raise ParcoursDoctoralNonTrouveException

        return ParcoursDoctoral(
            entity_id=entity_id,
            statut=ChoixStatutParcoursDoctoral[doctorate.post_enrolment_status],
            formation_id=FormationIdentity(doctorate.doctorate.acronym, doctorate.doctorate.academic_year.year),
            reference=doctorate.reference,
            matricule_doctorant=doctorate.candidate.global_id,
            bourse_recherche=BourseIdentity(uuid=str(doctorate.international_scholarship_id))
            if doctorate.international_scholarship_id
            else None,
            autre_bourse_recherche=doctorate.other_international_scholarship,
        )

    @classmethod
    def verifier_existence(cls, entity_id: 'ParcoursDoctoralIdentity') -> None:  # pragma: no cover
        doctorate: ParcoursDoctoral = ParcoursDoctoral.objects.filter(uuid=entity_id.uuid)
        if not doctorate:
            raise ParcoursDoctoralNonTrouveException

    @classmethod
    def save(cls, entity: 'ParcoursDoctoral') -> None:
        DoctorateAdmission.objects.update_or_create(
            uuid=entity.entity_id.uuid,
            defaults={'post_enrolment_status': entity.statut.name},
        )

    @classmethod
    def get_dto(cls, entity_id: 'ParcoursDoctoralIdentity') -> 'ParcoursDoctoralDTO':
        try:
            doctorate: ParcoursDoctoral = ParcoursDoctoral.objects.get(uuid=entity_id.uuid)
        except ParcoursDoctoral.DoesNotExist:
            raise ParcoursDoctoralNonTrouveException

        student: Optional[Student] = Student.objects.filter(person=doctorate.candidate).first()

        return ParcoursDoctoralDTO(
            uuid=str(entity_id.uuid),
            statut=ChoixStatutParcoursDoctoral[doctorate.post_enrolment_status].name,
            reference=doctorate.formatted_reference,
            matricule_doctorant=doctorate.candidate.global_id,
            nom_doctorant=doctorate.candidate.last_name,
            prenom_doctorant=doctorate.candidate.first_name,
            genre_doctorant=doctorate.candidate.gender,
            annee_formation=doctorate.doctorate.academic_year.year,
            sigle_formation=doctorate.doctorate.acronym,
            noma_doctorant=student.registration_id if student else '',
            intitule_formation=doctorate.doctorate.title
            if get_language() == settings.LANGUAGE_CODE_FR
            else doctorate.doctorate.title_english,
            type_admission=doctorate.type,
            titre_these=doctorate.project_title,
            type_financement=doctorate.financing_type,
            autre_bourse_recherche=doctorate.other_international_scholarship,
            bourse_recherche=BourseTranslator.build_dto(doctorate.international_scholarship)
            if doctorate.international_scholarship
            else None,
            admission_acceptee_le=None,  # TODO to add when the field will be added to the model
        )
