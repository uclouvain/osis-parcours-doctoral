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
from parcours_doctoral.ddd.epreuve_confirmation.commands import *
from parcours_doctoral.ddd.epreuve_confirmation.use_case.read import *
from parcours_doctoral.ddd.epreuve_confirmation.use_case.write import *
from parcours_doctoral.infrastructure.parcours_doctoral.domain.service.historique import (
    Historique,
)

from ..repository.parcours_doctoral import ParcoursDoctoralRepository
from .domain.service.notification import Notification
from .repository.epreuve_confirmation import EpreuveConfirmationRepository

COMMAND_HANDLERS = {
    RecupererEpreuvesConfirmationQuery: lambda msg_bus, cmd: recuperer_epreuves_confirmation(
        cmd,
        epreuve_confirmation_repository=EpreuveConfirmationRepository(),
    ),
    RecupererDerniereEpreuveConfirmationQuery: lambda msg_bus, cmd: recuperer_derniere_epreuve_confirmation(
        cmd,
        epreuve_confirmation_repository=EpreuveConfirmationRepository(),
    ),
    ModifierEpreuveConfirmationParCDDCommand: lambda msg_bus, cmd: modifier_epreuve_confirmation_par_cdd(
        cmd,
        epreuve_confirmation_repository=EpreuveConfirmationRepository(),
    ),
    SoumettreEpreuveConfirmationCommand: lambda msg_bus, cmd: soumettre_epreuve_confirmation(
        cmd,
        parcours_doctoral_repository=ParcoursDoctoralRepository(),
        epreuve_confirmation_repository=EpreuveConfirmationRepository(),
        notification=Notification(),
        historique=Historique(),
    ),
    CompleterEpreuveConfirmationParPromoteurCommand: lambda msg_bus, cmd: completer_epreuve_confirmation_par_promoteur(
        cmd,
        epreuve_confirmation_repository=EpreuveConfirmationRepository(),
        notification=Notification(),
    ),
    SoumettreReportDeDateCommand: lambda msg_bus, cmd: soumettre_report_de_date(
        cmd,
        epreuve_confirmation_repository=EpreuveConfirmationRepository(),
        notification=Notification(),
    ),
    SoumettreReportDeDateParCDDCommand: lambda msg_bus, cmd: soumettre_report_de_date(
        cmd,
        epreuve_confirmation_repository=EpreuveConfirmationRepository(),
        notification=Notification(),
    ),
    SoumettreAvisProlongationCommand: lambda msg_bus, cmd: soumettre_avis_prolongation(
        cmd,
        epreuve_confirmation_repository=EpreuveConfirmationRepository(),
    ),
    ConfirmerReussiteCommand: lambda msg_bus, cmd: confirmer_reussite(
        cmd,
        epreuve_confirmation_repository=EpreuveConfirmationRepository(),
        parcours_doctoral_repository=ParcoursDoctoralRepository(),
        notification=Notification(),
        historique=Historique(),
    ),
    ConfirmerEchecCommand: lambda msg_bus, cmd: confirmer_echec(
        cmd,
        epreuve_confirmation_repository=EpreuveConfirmationRepository(),
        parcours_doctoral_repository=ParcoursDoctoralRepository(),
        notification=Notification(),
        historique=Historique(),
    ),
    ConfirmerRepassageCommand: lambda msg_bus, cmd: confirmer_repassage(
        cmd,
        epreuve_confirmation_repository=EpreuveConfirmationRepository(),
        parcours_doctoral_repository=ParcoursDoctoralRepository(),
        notification=Notification(),
        historique=Historique(),
    ),
    TeleverserAvisRenouvellementMandatRechercheCommand: lambda msg_bus, cmd: televerser_avis_renouvellement_mandat_recherche(
        cmd,
        epreuve_confirmation_repository=EpreuveConfirmationRepository(),
    ),
}
