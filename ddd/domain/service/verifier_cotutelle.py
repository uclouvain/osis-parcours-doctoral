# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from osis_common.ddd import interface

from parcours_doctoral.ddd.domain.model._cotutelle import pas_de_cotutelle
from parcours_doctoral.ddd.domain.model.groupe_de_supervision import GroupeDeSupervision
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoral
from parcours_doctoral.ddd.domain.service.i_promoteur import IPromoteurTranslator
from parcours_doctoral.ddd.domain.validator.exceptions import (
    CotutelleDoitAvoirAuMoinsUnPromoteurExterneException,
)


class CotutellePossedePromoteurExterne(interface.DomainService):
    @classmethod
    def verifier(
        cls,
        parcours_doctoral: 'ParcoursDoctoral',
        groupe_de_supervision: 'GroupeDeSupervision',
        promoteur_translator: 'IPromoteurTranslator',
    ) -> None:
        aucun_externe = not any(
            promoteur_translator.est_externe(signature_promoteur.promoteur_id)
            for signature_promoteur in groupe_de_supervision.signatures_promoteurs
        )
        if parcours_doctoral.cotutelle and parcours_doctoral.cotutelle != pas_de_cotutelle and aucun_externe:
            raise CotutelleDoitAvoirAuMoinsUnPromoteurExterneException
