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
from admission.ddd.admission.doctorat.validation.builder.demande_identity import DemandeIdentityBuilder
from admission.ddd.admission.doctorat.validation.domain.model.demande import DemandeIdentity
from parcours_doctoral.ddd.builder.parcours_doctoral_identity import ParcoursDoctoralIdentityBuilder
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoralIdentity
from osis_common.ddd.interface import DomainService


class DemandeIdentityTranslator(DomainService):
    @classmethod
    def convertir_depuis_doctorat(cls, doctorat_id: ParcoursDoctoralIdentity) -> DemandeIdentity:
        return DemandeIdentityBuilder.build_from_uuid(doctorat_id.uuid)

    @classmethod
    def convertir_en_doctorat(cls, demande_id: DemandeIdentity) -> ParcoursDoctoralIdentity:
        return ParcoursDoctoralIdentityBuilder.build_from_uuid(demande_id.uuid)
