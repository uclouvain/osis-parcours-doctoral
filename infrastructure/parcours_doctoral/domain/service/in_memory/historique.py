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
from email.message import EmailMessage

from parcours_doctoral.ddd.domain.model.groupe_de_supervision import (
    GroupeDeSupervision,
    SignataireIdentity,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoral,
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.domain.service.i_historique import IHistorique


class HistoriqueInMemory(IHistorique):
    @classmethod
    def historiser_message_au_doctorant(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_emetteur: str,
        message: EmailMessage,
    ):
        pass

    @classmethod
    def historiser_initialisation(cls, parcours_doctoral: ParcoursDoctoralIdentity):
        pass

    @classmethod
    def historiser_demande_signatures(cls, parcours_doctoral: ParcoursDoctoral, matricule_auteur: str):
        pass

    @classmethod
    def historiser_designation_promoteur_reference(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        signataire_id: 'SignataireIdentity',
        matricule_auteur: str,
    ):
        pass

    @classmethod
    def historiser_ajout_membre(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        groupe_de_supervision: GroupeDeSupervision,
        signataire_id: 'SignataireIdentity',
        matricule_auteur: str,
    ):
        pass

    @classmethod
    def historiser_suppression_membre(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        groupe_de_supervision: GroupeDeSupervision,
        signataire_id: 'SignataireIdentity',
        matricule_auteur: str,
    ):
        pass

    @classmethod
    def historiser_modification_membre(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        signataire_id: 'SignataireIdentity',
        matricule_auteur: str,
    ):
        pass

    @classmethod
    def historiser_modification_projet(cls, parcours_doctoral: ParcoursDoctoral, matricule_auteur: str):
        pass

    @classmethod
    def historiser_modification_cotutelle(
        cls,
        parcours_doctoral_identity: ParcoursDoctoralIdentity,
        matricule_auteur: str,
    ):
        pass
