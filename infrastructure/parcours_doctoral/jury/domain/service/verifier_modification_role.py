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
from base.models.enums.entity_type import EntityType
from infrastructure.shared_kernel.personne_connue_ucl.personne_connue_ucl import PersonneConnueUclTranslator
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoralIdentity
from parcours_doctoral.ddd.domain.validator.exceptions import ParcoursDoctoralNonTrouveException, \
    ParcoursDoctoralSansCDDException
from parcours_doctoral.ddd.jury.domain.service.i_verifier_modification_role import IVerifierModificationRoleService
from parcours_doctoral.models import ParcoursDoctoral

SSS_ACRONYM = 'SSS'
SSH_ACRONYM = 'SSH'
SST_ACRONYM = 'SST'


class VerifierModificationRoleServiceService(IVerifierModificationRoleService):
    @classmethod
    def verifier(
        cls,
        parcours_doctoral_identity: 'ParcoursDoctoralIdentity',
        matricule_auteur: str,
    ) -> None:
        parcours_doctoral = ParcoursDoctoral.objects.select_related(
            'training__management_entity',
        ).filter(uuid=parcours_doctoral_identity.uuid).first()
        if parcours_doctoral is None:
            raise ParcoursDoctoralNonTrouveException

        auteur = PersonneConnueUclTranslator().get(matricule_auteur)

        if ProgramManager.objects.filter(
            education_group_id=parcours_doctoral.training.education_group_id,
            person=auteur,
        ).exists():
            # User is a CDD manager
            return

        cdd = parcours_doctoral.training.management_entity
        if cdd is None:
            raise ParcoursDoctoralSansCDDException

        if cdd.acronym == SSS_ACRONYM:
            # The student can change the roles
            if auteur != parcours_doctoral.student:
                raise
        elif cdd.acronym == SSH_ACRONYM:
            # The lead supervisor can change the roles
            pass
        elif cdd.acronym == SST_ACRONYM:
            # The auditor can change the roles
            pass
