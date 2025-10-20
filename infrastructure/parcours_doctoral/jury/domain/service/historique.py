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
from typing import Optional

from django.conf import settings
from django.utils import translation
from osis_history.utilities import add_history_entry

from infrastructure.shared_kernel.personne_connue_ucl.personne_connue_ucl import (
    PersonneConnueUclTranslator,
)
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoral
from parcours_doctoral.ddd.jury.domain.model.enums import RoleJury
from parcours_doctoral.ddd.jury.domain.model.jury import Jury, JuryIdentity, MembreJury
from parcours_doctoral.ddd.jury.domain.service.i_historique import IHistorique
from parcours_doctoral.ddd.jury.dtos.jury import AvisDTO
from parcours_doctoral.infrastructure.parcours_doctoral.jury.repository.jury import (
    JuryRepository,
)


class Historique(IHistorique):

    @classmethod
    def historiser_demande_signatures(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        jury: Jury,
        matricule_auteur: str,
    ):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            "Les demandes de signatures ont été envoyées.",
            "Signing requests have been sent.",
            "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
            tags=["parcours_doctoral", "jury", "status-changed"],
        )

    @classmethod
    def historiser_reinitialisation_signatures(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        jury: Jury,
        matricule_auteur: str,
    ):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            "Les signatures ont été réinitialisées.",
            "Signatures have been reset.",
            "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
            tags=["parcours_doctoral", "jury", "status-changed"],
        )

    @classmethod
    def historiser_avis(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        signataire: 'MembreJury',
        avis: AvisDTO,
        statut_original_proposition: 'ChoixStatutParcoursDoctoral',
        matricule_auteur: Optional[str] = '',
    ):
        if matricule_auteur:
            auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        else:
            auteur = signataire

        # Basculer en français pour la traduction de l'état
        with translation.override(settings.LANGUAGE_CODE_FR):
            if signataire.role == RoleJury.CDD:
                role = 'gestionnaire CDD'
            elif signataire.role == RoleJury.CDD:
                role = 'gestionnaire ADRE'
            elif signataire.est_promoteur:
                role = "promoteur"
            else:
                role = "membre du jury"
            message_fr = (
                "{signataire.prenom} {signataire.nom} a {action} la proposition {via_pdf}en tant que {role}".format(
                    signataire=signataire,
                    action="refusé" if avis.motif_refus else "approuvé",
                    via_pdf="via PDF " if avis.pdf else "",
                    role=role,
                )
            )
            details = []
            if avis.motif_refus:
                details.append("motif : {}".format(avis.motif_refus))
            if avis.commentaire_externe:
                details.append("commentaire : {}".format(avis.commentaire_externe))
            if details:
                details = " ({})".format(' ; '.join(details))
                message_fr += details

        # Anglais
        with translation.override(settings.LANGUAGE_CODE_EN):
            if signataire.role == RoleJury.CDD:
                role = 'PhD Committee manager'
            elif signataire.role == RoleJury.CDD:
                role = 'ADRE manager'
            elif signataire.est_promoteur:
                role = "promoter"
            else:
                role = "jury member"
            message_en = "{signataire.prenom} {signataire.nom} has {action} the proposition {via_pdf}as {role}".format(
                signataire=signataire,
                action="refused" if avis.motif_refus else "approved",
                via_pdf="via PDF " if avis.pdf else "",
                role=role,
            )
            details = []
            if avis.motif_refus:
                details.append("reason : {}".format(avis.motif_refus))
            if avis.commentaire_externe:
                details.append("comment : {}".format(avis.commentaire_externe))
            if details:
                details = " ({})".format('; '.join(details))
                message_en += details

        tags = ["parcours_doctoral", "jury"]

        if statut_original_proposition != parcours_doctoral.statut:
            tags.append("status-changed")

        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            message_fr,
            message_en,
            "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
            tags=tags,
        )
