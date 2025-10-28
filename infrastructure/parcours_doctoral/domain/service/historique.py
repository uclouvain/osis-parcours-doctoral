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
from email.message import EmailMessage
from typing import Optional

from django.conf import settings
from django.utils import translation
from osis_history.utilities import add_history_entry

from admission.infrastructure.utils import get_message_to_historize
from ddd.logic.shared_kernel.personne_connue_ucl.dtos import PersonneConnueUclDTO
from infrastructure.shared_kernel.personne_connue_ucl.personne_connue_ucl import (
    PersonneConnueUclTranslator,
)
from parcours_doctoral.ddd.domain.model._promoteur import PromoteurIdentity
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.domain.model.groupe_de_supervision import (
    GroupeDeSupervision,
    SignataireIdentity,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoral,
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.domain.service.i_historique import IHistorique
from parcours_doctoral.ddd.dtos import AvisDTO
from parcours_doctoral.infrastructure.parcours_doctoral.domain.service.membre_CA import (
    MembreCATranslator,
)
from parcours_doctoral.infrastructure.parcours_doctoral.domain.service.promoteur import (
    PromoteurTranslator,
)


class Historique(IHistorique):
    @classmethod
    def get_signataire(cls, signataire_id):
        if isinstance(signataire_id, PromoteurIdentity):
            return PromoteurTranslator.get_dto(signataire_id)
        return MembreCATranslator.get_dto(signataire_id)

    @classmethod
    def historiser_message_au_doctorant(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_emetteur: str,
        message: EmailMessage,
    ):
        emetteur = PersonneConnueUclTranslator.get(matricule_emetteur)

        message_a_historiser = get_message_to_historize(message)

        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            message_a_historiser[settings.LANGUAGE_CODE_FR],
            message_a_historiser[settings.LANGUAGE_CODE_EN],
            "{emetteur.prenom} {emetteur.nom}".format(emetteur=emetteur),
            tags=["parcours_doctoral", "message"],
        )

    @classmethod
    def historiser_initialisation(cls, parcours_doctoral_entity_id: ParcoursDoctoralIdentity):
        add_history_entry(
            parcours_doctoral_entity_id.uuid,
            "Le parcours doctoral a été initialisé.",
            "Doctoral training was initialized.",
            "",
            tags=["parcours_doctoral"],
        )

    @classmethod
    def historiser_demande_signatures(cls, parcours_doctoral: ParcoursDoctoral, matricule_auteur: str):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            "Les demandes de signatures ont été envoyées.",
            "Signing requests have been sent.",
            "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
            tags=["parcours_doctoral", "supervision", "status-changed"],
        )

    @classmethod
    def historiser_designation_promoteur_reference(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        signataire_id: 'SignataireIdentity',
        matricule_auteur: str,
    ):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        signataire = cls.get_signataire(signataire_id)
        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            "{membre.prenom} {membre.nom} a été désigné·e comme promoteur·trice de contact.".format(membre=signataire),
            "{membre.prenom} {membre.nom} has been designated as contact supervisor.".format(membre=signataire),
            "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
            tags=["parcours_doctoral", "supervision"],
        )

    @classmethod
    def historiser_ajout_membre(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        groupe_de_supervision: GroupeDeSupervision,
        signataire_id: 'SignataireIdentity',
        matricule_auteur: str,
    ):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        signataire = cls.get_signataire(signataire_id)
        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            "{membre.prenom} {membre.nom} a été ajouté en tant que {}.".format(
                "promoteur" if isinstance(signataire_id, PromoteurIdentity) else "membre du comité d'accompagnement",
                membre=signataire,
            ),
            "{membre.prenom} {membre.nom} has been added as {}.".format(
                "supervisor" if isinstance(signataire_id, PromoteurIdentity) else "supervision committee member",
                membre=signataire,
            ),
            "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
            tags=["parcours_doctoral", "supervision"],
        )

    @classmethod
    def historiser_suppression_membre(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        groupe_de_supervision: GroupeDeSupervision,
        signataire_id: 'SignataireIdentity',
        matricule_auteur: str,
    ):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        signataire = cls.get_signataire(signataire_id)
        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            "{membre.prenom} {membre.nom} a été retiré des {}.".format(
                "promoteurs" if isinstance(signataire_id, PromoteurIdentity) else "membres du comité d'accompagnement",
                membre=signataire,
            ),
            "{membre.prenom} {membre.nom} has been removed from {}.".format(
                "supervisors" if isinstance(signataire_id, PromoteurIdentity) else "supervision committee members",
                membre=signataire,
            ),
            "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
            tags=["parcours_doctoral", "supervision"],
        )

    @classmethod
    def historiser_modification_membre(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        signataire_id: 'SignataireIdentity',
        matricule_auteur: str,
    ):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        signataire = cls.get_signataire(signataire_id)
        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            "{membre.prenom} {membre.nom} a été modifié.".format(membre=signataire),
            "{membre.prenom} {membre.nom} has been updated.".format(membre=signataire),
            "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
            tags=["parcours_doctoral", "supervision"],
        )

    @classmethod
    def historiser_modification_projet(cls, parcours_doctoral: ParcoursDoctoral, matricule_auteur: str):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            "Le parcours doctoral a été modifié (Recherche).",
            "The doctoral training has been completed (Research).",
            "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
            tags=["parcours_doctoral", "modification"],
        )

    @classmethod
    def historiser_modification_cotutelle(
        self,
        parcours_doctoral_identity: ParcoursDoctoralIdentity,
        matricule_auteur: str,
    ):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        add_history_entry(
            parcours_doctoral_identity.uuid,
            "Le parcours doctoral a été modifié (Cotutelle).",
            "The doctoral training has been completed (Cotutelle).",
            "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
            tags=["parcours_doctoral", "modification"],
        )

    @classmethod
    def historiser_avis(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        signataire_id: 'SignataireIdentity',
        avis: AvisDTO,
        statut_original_parcours_doctoral: 'ChoixStatutParcoursDoctoral',
        matricule_auteur: Optional[str] = '',
    ):
        signataire = cls.get_signataire(signataire_id)
        if matricule_auteur:
            auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        else:
            auteur = signataire

        # Basculer en français pour la traduction de l'état
        with translation.override(settings.LANGUAGE_CODE_FR):
            message_fr = (
                "{signataire.prenom} {signataire.nom} a {action} la parcours_doctoral {via_pdf}en tant que {role}"
            ).format(
                signataire=signataire,
                action="refusé" if avis.motif_refus else "approuvé",
                via_pdf="via PDF " if avis.pdf else "",
                role=(
                    "promoteur" if isinstance(signataire_id, PromoteurIdentity) else "membre du comité d'accompagnement"
                ),
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
            message_en = (
                "{signataire.prenom} {signataire.nom} has {action} the parcours_doctoral {via_pdf}as {role}".format(
                    signataire=signataire,
                    action="refused" if avis.motif_refus else "approved",
                    via_pdf="via PDF " if avis.pdf else "",
                    role=(
                        "supervisor" if isinstance(signataire_id, PromoteurIdentity) else "supervision committee member"
                    ),
                )
            )
            details = []
            if avis.motif_refus:
                details.append("reason : {}".format(avis.motif_refus))
            if avis.commentaire_externe:
                details.append("comment : {}".format(avis.commentaire_externe))
            if details:
                details = " ({})".format('; '.join(details))
                message_en += details

        tags = ["parcours_doctoral", "supervision"]

        if statut_original_parcours_doctoral != parcours_doctoral.statut:
            tags.append("status-changed")

        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            message_fr,
            message_en,
            "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
            tags=tags,
        )

    @classmethod
    def historiser_repassage_epreuve_confirmation(cls, parcours_doctoral: ParcoursDoctoral, matricule_auteur: str):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            "La décision de l'épreuve de confirmation a été donnée : celle-ci doit être repassée.",
            "The decision of the confirmation paper exam has been made: it must be repeated.",
            "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
            tags=["parcours_doctoral", "confirmation", "status-changed"],
        )

    @classmethod
    def historiser_echec_epreuve_confirmation(cls, parcours_doctoral: ParcoursDoctoral, matricule_auteur: str):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            "La décision de l'épreuve de confirmation a été donnée : le candidat n'est pas autorisé à poursuivre.",
            "The decision of the confirmation paper exam has been made: the candidate is not authorized to continue.",
            "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
            tags=["parcours_doctoral", "confirmation", "status-changed"],
        )

    @classmethod
    def historiser_reussite_epreuve_confirmation(cls, parcours_doctoral: ParcoursDoctoral, matricule_auteur: str):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            "La décision de l'épreuve de confirmation a été donnée : celle-ci a été réussie.",
            "The decision of the confirmation paper exam has been made: it has been passed.",
            "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
            tags=["parcours_doctoral", "confirmation", "status-changed"],
        )

    @classmethod
    def historiser_soumission_epreuve_confirmation(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_auteur: str,
        statut_original_parcours_doctoral: ChoixStatutParcoursDoctoral,
    ):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        tags = ["parcours_doctoral", "confirmation"]

        if parcours_doctoral.statut != statut_original_parcours_doctoral:
            tags.append("status-changed")

        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            "Le candidat a renseigné des informations relatives à son épreuve de confirmation.",
            "The candidate has filled in information relating to his confirmation paper exam.",
            "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
            tags=tags,
        )

    @classmethod
    def historiser_soumission_recevabilite(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_auteur: str,
        statut_original_parcours_doctoral: ChoixStatutParcoursDoctoral,
    ):
        if parcours_doctoral.statut != statut_original_parcours_doctoral:
            auteur = PersonneConnueUclTranslator().get(matricule_auteur)
            tags = ["parcours_doctoral", "admissibility", "status-changed"]

            add_history_entry(
                parcours_doctoral.entity_id.uuid,
                "Le doctorant a renseigné des informations relatives à la recevabilité.",
                "The doctoral student has filled in information relating to the admissibility.",
                "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
                tags=tags,
            )

    @classmethod
    def historiser_soumission_defense_privee(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_auteur: str,
        statut_original_parcours_doctoral: ChoixStatutParcoursDoctoral,
    ):
        if parcours_doctoral.statut != statut_original_parcours_doctoral:
            auteur = PersonneConnueUclTranslator().get(matricule_auteur)
            tags = ["parcours_doctoral", "private-defense", "status-changed"]

            add_history_entry(
                parcours_doctoral.entity_id.uuid,
                "Le doctorant a renseigné des informations relatives à la défense privée.",
                "The doctoral student has filled in information relating to the private defence.",
                "{auteur.prenom} {auteur.nom}".format(auteur=auteur),
                tags=tags,
            )

    @classmethod
    def historiser_soumission_proces_verbal_defense_privee(
        cls,
        parcours_doctoral_identity: ParcoursDoctoralIdentity,
        matricule_auteur: str,
    ):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)

        add_history_entry(
            parcours_doctoral_identity.uuid,
            'Le procès verbal de la défense privée a été modifié.',
            'The minutes of the private defence have been updated.',
            '{auteur.prenom} {auteur.nom}'.format(auteur=auteur),
            tags=['parcours_doctoral', 'private-defense'],
        )

    @classmethod
    def historiser_autorisation_defense_privee(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_auteur: str,
    ):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)

        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            'La défense privée a été autorisée.',
            'The private defence has been authorised.',
            '{auteur.prenom} {auteur.nom}'.format(auteur=auteur),
            tags=['parcours_doctoral', 'private-defense', 'status-changed'],
        )

    @classmethod
    def historiser_invitation_jury_defense_privee(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        auteur: PersonneConnueUclDTO,
    ):
        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            'Les membres du jury ont été invités à la défense privée.',
            'The jury members have been invited to the private defence.',
            '{auteur.prenom} {auteur.nom}'.format(auteur=auteur),
            tags=['parcours_doctoral', 'private-defense'],
        )

    @classmethod
    def historiser_decision_reussie_defense_privee(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_auteur: str,
    ):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            'La décision de la défense privée a été donnée : celle-ci a été réussie.',
            'The decision of the private defence has been made: it has been passed.',
            '{auteur.prenom} {auteur.nom}'.format(auteur=auteur),
            tags=['parcours_doctoral', 'private-defense', 'status-changed'],
        )

    @classmethod
    def historiser_decision_echec_defense_privee(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_auteur: str,
    ):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            'La décision de la défense privée a été donnée : le candidat n\'est pas autorisé à poursuivre.',
            'The decision of the private defence has been made: the candidate is not authorized to continue.',
            '{auteur.prenom} {auteur.nom}'.format(auteur=auteur),
            tags=['parcours_doctoral', 'private-defense', 'status-changed'],
        )

    @classmethod
    def historiser_decision_repetition_defense_privee(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_auteur: str,
    ):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            'La décision de la défense privée a été donnée : celle-ci doit être repassée.',
            'The decision of the private defence has been made: it must be repeated.',
            '{auteur.prenom} {auteur.nom}'.format(auteur=auteur),
            tags=['parcours_doctoral', 'private-defense', 'status-changed'],
        )

    @classmethod
    def historiser_modification_defense_privee(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_auteur: str,
    ):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)
        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            'La défense privée a été modifiée.',
            'The private defence has been updated.',
            '{auteur.prenom} {auteur.nom}'.format(auteur=auteur),
            tags=['parcours_doctoral', 'private-defense'],
        )

    @classmethod
    def historiser_soumission_soutenance_publique(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_auteur: str,
        statut_original_parcours_doctoral: ChoixStatutParcoursDoctoral,
    ):
        if parcours_doctoral.statut != statut_original_parcours_doctoral:
            auteur = PersonneConnueUclTranslator().get(matricule_auteur)
            tags = ['parcours_doctoral', 'public-defense', 'status-changed']

            add_history_entry(
                parcours_doctoral.entity_id.uuid,
                'Le doctorant a renseigné des informations relatives à la soutenance publique.',
                'The doctoral student has filled in information relating to the public defence.',
                '{auteur.prenom} {auteur.nom}'.format(auteur=auteur),
                tags=tags,
            )

    @classmethod
    def historiser_autorisation_soutenance_publique(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_auteur: str,
    ):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)

        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            'La soutenance publique a été autorisée.',
            'The public defence has been authorised.',
            '{auteur.prenom} {auteur.nom}'.format(auteur=auteur),
            tags=['parcours_doctoral', 'public-defense', 'status-changed'],
        )

    @classmethod
    def historiser_decision_reussie_soutenance_publique(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_auteur: str,
    ):
        auteur = PersonneConnueUclTranslator().get(matricule_auteur)

        add_history_entry(
            parcours_doctoral.entity_id.uuid,
            'La décision de la soutenance publique a été donnée : celle-ci a été réussie.',
            'The decision of the public defence has been made: it has been passed.',
            '{auteur.prenom} {auteur.nom}'.format(auteur=auteur),
            tags=['parcours_doctoral', 'public-defense', 'status-changed'],
        )
