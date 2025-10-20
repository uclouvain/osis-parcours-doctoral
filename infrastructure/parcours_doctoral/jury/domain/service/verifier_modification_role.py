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
from base.auth.roles.program_manager import ProgramManager
from infrastructure.shared_kernel.personne_connue_ucl.personne_connue_ucl import (
    PersonneConnueUclTranslator,
)
from parcours_doctoral.auth.roles.auditor import Auditor
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.domain.validator.exceptions import (
    ParcoursDoctoralNonTrouveException,
)
from parcours_doctoral.ddd.jury.domain.model.enums import RoleJury
from parcours_doctoral.ddd.jury.domain.service.i_verifier_modification_role import (
    IVerifierModificationRoleService,
)
from parcours_doctoral.ddd.jury.domain.validator.exceptions import (
    ModificationRoleImpossibleSSHException,
    ModificationRoleImpossibleSSSException,
    ModificationRoleImpossibleSSTException,
    RolesNonAttribueException,
    TropDeRolesAttribuesException,
)
from parcours_doctoral.models import ParcoursDoctoral

SSS_ACRONYM = 'SSS'
SSH_ACRONYM = 'SSH'
SST_ACRONYM = 'SST'


class VerifierModificationRoleServiceService(IVerifierModificationRoleService):
    @classmethod
    def _get_parcours_doctoral(cls, parcours_doctoral_identity: 'ParcoursDoctoralIdentity'):
        parcours_doctoral = (
            ParcoursDoctoral.objects.annotate_secteur_formation()
            .prefetch_related('jury_group__actors__juryactor')
            .filter(uuid=parcours_doctoral_identity.uuid)
            .first()
        )
        if parcours_doctoral is None:
            raise ParcoursDoctoralNonTrouveException
        return parcours_doctoral

    @classmethod
    def verifier(
        cls,
        parcours_doctoral_identity: 'ParcoursDoctoralIdentity',
        matricule_auteur: str,
    ) -> None:
        parcours_doctoral = cls._get_parcours_doctoral(parcours_doctoral_identity)

        if ProgramManager.objects.filter(
            education_group_id=parcours_doctoral.training.education_group_id,
            person__global_id=matricule_auteur,
        ).exists():
            # User is a CDD manager
            return

        if parcours_doctoral.sigle_secteur_formation == SSS_ACRONYM:
            # The student can change the roles
            if matricule_auteur != parcours_doctoral.student.global_id:
                raise ModificationRoleImpossibleSSSException
        elif parcours_doctoral.sigle_secteur_formation == SSH_ACRONYM:
            # The lead supervisor can change the roles
            if not parcours_doctoral.supervision_group.actors.filter(
                person__global_id=matricule_auteur,
                parcoursdoctoralsupervisionactor__is_reference_promoter=True,
            ).exists():
                raise ModificationRoleImpossibleSSHException
        elif parcours_doctoral.sigle_secteur_formation == SST_ACRONYM:
            # The auditor can change the roles
            if not Auditor.objects.filter(person__global_id=matricule_auteur).exists():
                raise ModificationRoleImpossibleSSTException

    @classmethod
    def verifier_tous_les_roles_attribués(
        cls,
        parcours_doctoral_identity: 'ParcoursDoctoralIdentity',
        matricule_auteur: str,
    ) -> None:
        if not matricule_auteur:
            return

        parcours_doctoral = cls._get_parcours_doctoral(parcours_doctoral_identity)

        has_president = any(
            actor.juryactor.role == RoleJury.PRESIDENT.name for actor in parcours_doctoral.jury_group.actors.all()
        )
        has_secretary = any(
            actor.juryactor.role == RoleJury.SECRETAIRE.name for actor in parcours_doctoral.jury_group.actors.all()
        )

        if has_president and has_secretary:
            return

        if parcours_doctoral.sigle_secteur_formation == SSS_ACRONYM:
            # The student can change the roles
            return
        elif parcours_doctoral.sigle_secteur_formation == SSH_ACRONYM:
            # The lead supervisor can change the roles
            if parcours_doctoral.supervision_group.actors.filter(
                person__global_id=matricule_auteur,
                parcoursdoctoralsupervisionactor__is_reference_promoter=True,
            ).exists():
                raise RolesNonAttribueException
        elif parcours_doctoral.sigle_secteur_formation == SST_ACRONYM:
            # The auditor can change the roles
            if Auditor.objects.filter(person__global_id=matricule_auteur).exists():
                raise RolesNonAttribueException

    @classmethod
    def verifier_roles_pour_cdd(
        cls,
        parcours_doctoral_identity: 'ParcoursDoctoralIdentity',
    ) -> None:
        parcours_doctoral = cls._get_parcours_doctoral(parcours_doctoral_identity)

        presidents = [
            actor for actor in parcours_doctoral.jury_group.actors.all() if actor.juryactor.role == RoleJury.PRESIDENT.name
        ]
        secretaries = [
            actor for actor in parcours_doctoral.jury_group.actors.all() if actor.juryactor.role == RoleJury.SECRETAIRE.name
        ]

        if not presidents or not secretaries:
            raise RolesNonAttribueException

        if len(presidents) > 1 or len(secretaries) > 1:
            raise TropDeRolesAttribuesException
