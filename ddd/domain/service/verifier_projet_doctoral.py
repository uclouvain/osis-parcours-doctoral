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
from functools import partial
from typing import List

from admission.ddd.admission.domain.model.question_specifique import QuestionSpecifique
from admission.ddd.admission.domain.service.verifier_questions_specifiques import (
    VerifierQuestionsSpecifiques,
)
from base.ddd.utils.business_validator import execute_functions_and_aggregate_exceptions
from osis_common.ddd import interface

from parcours_doctoral.ddd.domain.model.groupe_de_supervision import GroupeDeSupervision
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoral
from parcours_doctoral.ddd.domain.service.i_promoteur import IPromoteurTranslator
from parcours_doctoral.ddd.domain.service.verifier_cotutelle import (
    CotutellePossedePromoteurExterne,
)
from parcours_doctoral.ddd.domain.service.verifier_promoteur import (
    GroupeDeSupervisionPossedeUnPromoteurMinimum,
)


class VerifierPropositionProjetDoctoral(interface.DomainService):
    @classmethod
    def verifier(
        cls,
        parcours_doctoral_candidat: ParcoursDoctoral,
        groupe_de_supervision: GroupeDeSupervision,
        questions_specifiques: List[QuestionSpecifique],
        promoteur_translator: IPromoteurTranslator,
    ) -> None:
        execute_functions_and_aggregate_exceptions(
            parcours_doctoral_candidat.verifier_projet_doctoral,
            partial(GroupeDeSupervisionPossedeUnPromoteurMinimum.verifier, groupe_de_supervision, promoteur_translator),
            partial(
                CotutellePossedePromoteurExterne.verifier,
                parcours_doctoral_candidat,
                groupe_de_supervision,
                promoteur_translator,
            ),
            groupe_de_supervision.verifier_signataires,
            partial(
                VerifierQuestionsSpecifiques.verifier_onglet_choix_formation,
                parcours_doctoral_candidat,
                questions_specifiques,
            ),
        )
