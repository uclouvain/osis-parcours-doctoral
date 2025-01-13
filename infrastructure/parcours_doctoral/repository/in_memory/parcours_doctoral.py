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
from typing import List

from attr import dataclass
from django.utils import timezone

from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixGenre
from base.ddd.utils.in_memory_repository import InMemoryGenericRepository
from infrastructure.reference.domain.service.in_memory.bourse import (
    BourseInMemoryTranslator,
)
from parcours_doctoral.ddd.domain.model.enums import ChoixTypeFinancement
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoral,
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.domain.validator.exceptions import (
    ParcoursDoctoralNonTrouveException,
)
from parcours_doctoral.ddd.dtos import (
    EntiteGestionDTO,
    FormationDTO,
    ParcoursDoctoralDTO,
    ParcoursDoctoralRechercheDTO,
)
from parcours_doctoral.ddd.dtos.parcours_doctoral import (
    CotutelleDTO,
    FinancementDTO,
    ProjetDTO,
)
from parcours_doctoral.ddd.epreuve_confirmation.domain.model.epreuve_confirmation import (
    EpreuveConfirmation,
)
from parcours_doctoral.ddd.repository.i_parcours_doctoral import (
    IParcoursDoctoralRepository,
)
from parcours_doctoral.ddd.test.factory.parcours_doctoral import (
    ParcoursDoctoralECGE3DPMinimaleFactory,
    ParcoursDoctoralESP3DPMinimaleFactory,
    ParcoursDoctoralPreSC3DPAvecPromoteursEtMembresCADejaApprouvesAccepteeFactory,
    ParcoursDoctoralSC3DPAvecMembresEtCotutelleFactory,
    ParcoursDoctoralSC3DPAvecMembresFactory,
    ParcoursDoctoralSC3DPAvecMembresInvitesFactory,
    ParcoursDoctoralSC3DPAvecPromoteurDejaApprouveFactory,
    ParcoursDoctoralSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactory,
    ParcoursDoctoralSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactoryRejeteeCDDFactory,
    ParcoursDoctoralSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
    ParcoursDoctoralSC3DPMinimaleCotutelleAvecPromoteurExterneFactory,
    ParcoursDoctoralSC3DPMinimaleCotutelleSansPromoteurExterneFactory,
    ParcoursDoctoralSC3DPMinimaleFactory,
    ParcoursDoctoralSC3DPMinimaleSansCotutelleFactory,
    ParcoursDoctoralSC3DPMinimaleSansDetailProjetFactory,
    ParcoursDoctoralSC3DPMinimaleSansFinancementFactory,
    ParcoursDoctoralSC3DPSansMembreCAFactory,
    ParcoursDoctoralSC3DPSansPromoteurFactory,
    ParcoursDoctoralSC3DPSansPromoteurReferenceFactory,
)


@dataclass
class Doctorant:
    matricule: str
    prenom: str
    nom: str
    noma: str
    genre: ChoixGenre


@dataclass
class Formation:
    intitule: str
    sigle: str
    annee: int
    campus: str


class ParcoursDoctoralInMemoryRepository(InMemoryGenericRepository, IParcoursDoctoralRepository):
    entities: List[ParcoursDoctoral] = list()
    doctorants = [
        Doctorant("1", "Jean", "Dupont", "01", ChoixGenre.H),
        Doctorant("2", "Michel", "Durand", "02", ChoixGenre.H),
        Doctorant("3", "Pierre", "Dupond", "03", ChoixGenre.H),
    ]

    formations = [
        Formation("Doctorat en sciences", "SC3DP", 2022, "Mons"),
        Formation("Doctorat en sciences économiques et de gestion", "ECGM3D", 2022, "Mons"),
    ]

    @classmethod
    def get(cls, entity_id: 'ParcoursDoctoralIdentity') -> 'ParcoursDoctoral':
        parcours_doctoral = super().get(entity_id)
        if not parcours_doctoral:
            raise ParcoursDoctoralNonTrouveException
        return parcours_doctoral

    @classmethod
    def verifier_existence(cls, entity_id: 'ParcoursDoctoralIdentity') -> None:
        parcours_doctoral = super().get(entity_id)
        if not parcours_doctoral:
            raise ParcoursDoctoralNonTrouveException

    @classmethod
    def get_dto(cls, entity_id: 'ParcoursDoctoralIdentity') -> 'ParcoursDoctoralDTO':
        parcours_doctoral = cls.get(entity_id)
        doctorant = next(
            d for d in cls.doctorants if d.matricule == parcours_doctoral.matricule_doctorant
        )  # pragma: no branch
        formation = next(
            f for f in cls.formations if f.sigle == parcours_doctoral.formation_id.sigle
        )  # pragma: no branch
        bourse_recherche_dto = (
            BourseInMemoryTranslator.get_dto(uuid=str(parcours_doctoral.financement.bourse_recherche.uuid))
            if parcours_doctoral.financement.bourse_recherche
            else None
        )

        return ParcoursDoctoralDTO(
            uuid=str(entity_id.uuid),
            statut=parcours_doctoral.statut.name,
            date_changement_statut=None,
            reference=str(parcours_doctoral.reference),
            matricule_doctorant=parcours_doctoral.matricule_doctorant,
            noma_doctorant=doctorant.noma,
            photo_identite_doctorant=['foo'],
            nom_doctorant=doctorant.nom,
            prenom_doctorant=doctorant.prenom,
            formation=FormationDTO(
                annee=formation.annee,
                sigle=formation.sigle,
                intitule=formation.intitule,
                code='',
                intitule_fr=formation.intitule,
                intitule_en='',
                entite_gestion=EntiteGestionDTO(
                    sigle='',
                    intitule='',
                    lieu='',
                    code_postal='',
                    ville='',
                    pays='',
                    numero_telephone='',
                    code_secteur='',
                    intitule_secteur='',
                ),
                campus=None,
                type='',
            ),
            financement=FinancementDTO(
                type=parcours_doctoral.financement.type.name if parcours_doctoral.financement.type else None,
                type_contrat_travail=parcours_doctoral.financement.type_contrat_travail,
                eft=parcours_doctoral.financement.eft,
                bourse_recherche=bourse_recherche_dto,
                autre_bourse_recherche=parcours_doctoral.financement.autre_bourse_recherche,
                bourse_date_debut=parcours_doctoral.financement.bourse_date_debut,
                bourse_date_fin=parcours_doctoral.financement.bourse_date_fin,
                bourse_preuve=parcours_doctoral.financement.bourse_preuve,
                duree_prevue=parcours_doctoral.financement.duree_prevue,
                temps_consacre=parcours_doctoral.financement.temps_consacre,
                est_lie_fnrs_fria_fresh_csc=parcours_doctoral.financement.est_lie_fnrs_fria_fresh_csc,
                commentaire=parcours_doctoral.financement.commentaire,
            ),
            genre_doctorant=doctorant.genre.name,
            projet=ProjetDTO(
                titre='titre',
                resume='resume',
                langue_redaction_these='FR',
                nom_langue_redaction_these='Francais',
                institut_these=None,
                nom_institut_these='institut',
                sigle_institut_these='INST',
                lieu_these='lieu',
                projet_doctoral_deja_commence=None,
                projet_doctoral_institution='',
                projet_doctoral_date_debut=None,
                documents_projet=[],
                graphe_gantt=[],
                proposition_programme_doctoral=[],
                projet_formation_complementaire=[],
                lettres_recommandation=[],
                doctorat_deja_realise='',
                institution='',
                domaine_these='domaine',
                date_soutenance=None,
                raison_non_soutenue='raison',
            ),
            cotutelle=CotutelleDTO(
                cotutelle=False,
                motivation='',
                institution_fwb=None,
                institution='',
                autre_institution=None,
                autre_institution_nom='',
                autre_institution_adresse='',
                demande_ouverture=[],
                convention=[],
                autres_documents=[],
            ),
            cree_le=timezone.now(),
            commission_proximite='',
        )

    @classmethod
    def get_cotutelle_dto(cls, entity_id: 'ParcoursDoctoralIdentity') -> 'CotutelleDTO':
        return cls.get_dto(entity_id).cotutelle

    @classmethod
    def reset(cls):
        cls.entities = [
            ParcoursDoctoralSC3DPMinimaleFactory(),
            ParcoursDoctoralECGE3DPMinimaleFactory(),
            ParcoursDoctoralESP3DPMinimaleFactory(),
            ParcoursDoctoralSC3DPMinimaleSansDetailProjetFactory(),
            ParcoursDoctoralSC3DPMinimaleSansFinancementFactory(),
            ParcoursDoctoralSC3DPMinimaleSansCotutelleFactory(),
            ParcoursDoctoralSC3DPMinimaleCotutelleSansPromoteurExterneFactory(),
            ParcoursDoctoralSC3DPMinimaleCotutelleAvecPromoteurExterneFactory(),
            ParcoursDoctoralPreSC3DPAvecPromoteursEtMembresCADejaApprouvesAccepteeFactory(),
            ParcoursDoctoralSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactoryRejeteeCDDFactory(),
            ParcoursDoctoralSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory(),
            ParcoursDoctoralSC3DPAvecMembresFactory(),
            ParcoursDoctoralSC3DPAvecMembresEtCotutelleFactory(),
            ParcoursDoctoralSC3DPAvecMembresInvitesFactory(),
            ParcoursDoctoralSC3DPSansPromoteurFactory(),
            ParcoursDoctoralSC3DPSansPromoteurReferenceFactory(),
            ParcoursDoctoralSC3DPSansMembreCAFactory(),
            ParcoursDoctoralSC3DPAvecPromoteurDejaApprouveFactory(),
            ParcoursDoctoralSC3DPAvecPromoteurRefuseEtMembreCADejaApprouveFactory(),
        ]

    @classmethod
    def _get_search_dto(cls, parcours_doctoral: 'ParcoursDoctoral') -> 'ParcoursDoctoralRechercheDTO':
        doctorant = next(d for d in cls.doctorants if d.matricule == parcours_doctoral.matricule_doctorant)
        formation = next(f for f in cls.formations if f.sigle == parcours_doctoral.formation_id.sigle)

        return ParcoursDoctoralRechercheDTO(
            uuid=parcours_doctoral.entity_id.uuid,
            reference=str(parcours_doctoral.reference),
            statut=parcours_doctoral.statut.name,
            formation=FormationDTO(
                annee=formation.annee,
                sigle=formation.sigle,
                intitule=formation.intitule,
                code='',
                intitule_fr=formation.intitule,
                intitule_en='',
                entite_gestion=EntiteGestionDTO(
                    sigle='',
                    intitule='',
                    lieu='',
                    code_postal='',
                    ville='',
                    pays='',
                    numero_telephone='',
                    code_secteur='',
                    intitule_secteur='',
                ),
                campus=None,
                type='',
            ),
            matricule_doctorant=parcours_doctoral.matricule_doctorant,
            genre_doctorant=doctorant.genre,
            prenom_doctorant=doctorant.prenom,
            nom_doctorant=doctorant.nom,
            cree_le=timezone.now(),
        )

    @classmethod
    def search_dto(
        cls,
        matricule_etudiant: str = None,
        matricule_membre: str = None,
    ) -> List['ParcoursDoctoralRechercheDTO']:
        return [
            cls._get_search_dto(parcours_doctoral)
            for parcours_doctoral in cls.entities
            if parcours_doctoral.matricule_doctorant == matricule_etudiant
        ]
