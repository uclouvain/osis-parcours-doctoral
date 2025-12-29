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
from typing import List

from ddd.logic.parcours_interne.dto.info import ProprietesPaeDTO
from parcours_doctoral.ddd.defense_privee.dtos import DefensePriveeDTO
from parcours_doctoral.ddd.domain.service.i_pdf_generation import IPDFGeneration
from parcours_doctoral.ddd.dtos import GroupeDeSupervisionDTO, ParcoursDoctoralDTO
from parcours_doctoral.ddd.epreuve_confirmation.dtos import EpreuveConfirmationDTO
from parcours_doctoral.ddd.formation.dtos import CoursDTO
from parcours_doctoral.ddd.jury.dtos.jury import JuryDTO
from parcours_doctoral.ddd.recevabilite.dtos import RecevabiliteDTO
from parcours_doctoral.exports.utils import parcours_doctoral_generate_pdf


class PDFGeneration(IPDFGeneration):
    @classmethod
    def generer_pdf_archive(
        cls,
        parcours_doctoral: ParcoursDoctoralDTO,
        groupe_supervision: GroupeDeSupervisionDTO,
        epreuves_confirmation: List[EpreuveConfirmationDTO],
        jury: JuryDTO,
        cours_complementaires: List[CoursDTO],
        proprietes_pae: List['ProprietesPaeDTO'],
        defenses_privees: List[DefensePriveeDTO],
        recevabilites: List[RecevabiliteDTO],
    ) -> str:
        try:
            propriete_pae = proprietes_pae[0]
        except IndexError:
            propriete_pae = None
        context = {
            'parcours_doctoral': parcours_doctoral,
            'groupe_supervision': groupe_supervision,
            'epreuves_confirmation': epreuves_confirmation,
            'jury': jury,
            'cours_complementaires': cours_complementaires,
            'propriete_pae': propriete_pae,
            'defenses_privees': defenses_privees,
            'recevabilites': recevabilites,
        }

        # Generate the pdf
        save_token = parcours_doctoral_generate_pdf(
            template='parcours_doctoral/exports/archive.html',
            filename='parcours_doctoral.pdf',
            context=context,
        )
        return save_token
