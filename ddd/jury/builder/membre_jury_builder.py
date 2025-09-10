##############################################################################
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
##############################################################################
from osis_common.ddd import interface
from parcours_doctoral.ddd.jury.commands import (
    AjouterMembreCommand,
    ModifierJuryCommand,
    ModifierMembreCommand,
)
from parcours_doctoral.ddd.jury.domain.model.enums import GenreMembre, TitreMembre
from parcours_doctoral.ddd.jury.domain.model.jury import MembreJury


class MembreJuryBuilder(interface.RootEntityBuilder):
    @classmethod
    def build_from_repository_dto(cls, dto_object: 'interface.DTO') -> 'MembreJury':
        raise NotImplementedError

    @classmethod
    def build_from_command(cls, cmd: 'ModifierJuryCommand'):  # type: ignore[override]
        raise NotImplementedError

    @classmethod
    def build_from_ajouter_membre_command(
        cls,
        cmd: 'AjouterMembreCommand',
    ) -> 'MembreJury':
        return MembreJury(
            est_promoteur=False,
            est_promoteur_de_reference=False,
            matricule=cmd.matricule,
            institution=cmd.institution,
            autre_institution=cmd.autre_institution,
            pays=cmd.pays,
            nom=cmd.nom,
            prenom=cmd.prenom,
            titre=TitreMembre[cmd.titre] if cmd.titre else None,
            justification_non_docteur=cmd.justification_non_docteur,
            genre=GenreMembre[cmd.genre] if cmd.genre else None,
            langue=cmd.langue,
            email=cmd.email,
        )

    @classmethod
    def build_from_modifier_membre_command(
        cls,
        cmd: 'ModifierMembreCommand',
    ) -> 'MembreJury':
        return MembreJury(
            est_promoteur=False,
            est_promoteur_de_reference=False,
            uuid=cmd.uuid_membre,
            matricule=cmd.matricule,
            institution=cmd.institution,
            autre_institution=cmd.autre_institution,
            pays=cmd.pays,
            nom=cmd.nom,
            prenom=cmd.prenom,
            titre=TitreMembre[cmd.titre] if cmd.titre else None,
            justification_non_docteur=cmd.justification_non_docteur,
            genre=GenreMembre[cmd.genre] if cmd.genre else None,
            langue=cmd.langue,
            email=cmd.email,
        )
