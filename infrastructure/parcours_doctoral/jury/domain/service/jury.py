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
from django.utils.timezone import now

from base.auth.roles.program_manager import ProgramManager
from base.models.enums.mandate_type import MandateTypes
from base.models.mandatary import Mandatary
from parcours_doctoral.auth.roles.adre_manager import AdreManager
from parcours_doctoral.auth.roles.auditor import Auditor
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.jury.domain.model.enums import RoleJury
from parcours_doctoral.ddd.jury.domain.model.jury import MembreJury, SignatureMembre
from parcours_doctoral.ddd.jury.domain.service.i_jury import IJuryService
from parcours_doctoral.ddd.jury.domain.validator.exceptions import (
    AuteurNonAdreException,
    AuteurNonCddException,
    PasDeVerificateurException,
)
from parcours_doctoral.infrastructure.parcours_doctoral.jury.repository.jury import (
    INSTITUTION_UCL,
)
from parcours_doctoral.models import ParcoursDoctoral


class JuryService(IJuryService):
    @classmethod
    def recuperer_verificateur(
        cls,
        parcours_doctoral_id: ParcoursDoctoralIdentity,
    ) -> MembreJury:
        entity = (
            ParcoursDoctoral.objects.select_related('thesis_institute__entity').get(uuid=parcours_doctoral_id.uuid)
        ).thesis_institute.entity
        verificateur = Auditor.objects.filter(entity=entity).first()
        if verificateur is None:
            raise PasDeVerificateurException()
        return MembreJury(
            role=RoleJury.VERIFICATEUR,
            est_promoteur=False,
            est_promoteur_de_reference=False,
            matricule=verificateur.person.global_id,
            institution=INSTITUTION_UCL,
            autre_institution='',
            pays=str(verificateur.person.country_of_citizenship),
            nom=verificateur.person.last_name,
            prenom=verificateur.person.first_name,
            titre=None,
            justification_non_docteur='',
            genre=verificateur.person.gender,
            langue=verificateur.person.language,
            email=verificateur.person.email,
            signature=SignatureMembre(),
        )

    @classmethod
    def recuperer_gestionnaire_cdd(
        cls,
        parcours_doctoral_id: ParcoursDoctoralIdentity,
        matricule: str,
    ) -> MembreJury:
        gestionnaire_cdd = (
            ProgramManager.objects.filter(
                education_group__in=ParcoursDoctoral.objects.filter(uuid=parcours_doctoral_id.uuid).values(
                    'training__education_group'
                ),
                person__global_id=matricule,
            )
            .select_related('person')
            .first()
        )
        if gestionnaire_cdd is None:
            raise AuteurNonCddException()
        gestionnaire_cdd = gestionnaire_cdd.person
        return MembreJury(
            role=RoleJury.CDD,
            est_promoteur=False,
            est_promoteur_de_reference=False,
            matricule=gestionnaire_cdd.global_id,
            institution=INSTITUTION_UCL,
            autre_institution='',
            pays=str(gestionnaire_cdd.country_of_citizenship),
            nom=gestionnaire_cdd.last_name,
            prenom=gestionnaire_cdd.first_name,
            titre=None,
            justification_non_docteur='',
            genre=gestionnaire_cdd.gender,
            langue=gestionnaire_cdd.language,
            email=gestionnaire_cdd.email,
            signature=SignatureMembre(),
        )

    @classmethod
    def recuperer_gestionnaire_adre(
        cls,
        parcours_doctoral_id: ParcoursDoctoralIdentity,
        matricule: str,
    ) -> MembreJury:
        gestionnaire_adre = (
            AdreManager.objects.filter(
                person__global_id=matricule,
            )
            .select_related('person')
            .first()
        )
        if gestionnaire_adre is None:
            raise AuteurNonAdreException()
        gestionnaire_adre = gestionnaire_adre.person
        return MembreJury(
            role=RoleJury.ADRE,
            est_promoteur=False,
            est_promoteur_de_reference=False,
            matricule=gestionnaire_adre.global_id,
            institution=INSTITUTION_UCL,
            autre_institution='',
            pays=str(gestionnaire_adre.country_of_citizenship),
            nom=gestionnaire_adre.last_name,
            prenom=gestionnaire_adre.first_name,
            titre=None,
            justification_non_docteur='',
            genre=gestionnaire_adre.gender,
            langue=gestionnaire_adre.language,
            email=gestionnaire_adre.email,
            signature=SignatureMembre(),
        )
