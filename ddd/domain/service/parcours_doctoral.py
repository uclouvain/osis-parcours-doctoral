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
from admission.ddd.admission.doctorat.preparation.domain.model.groupe_de_supervision import GroupeDeSupervision
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import Proposition
from parcours_doctoral.ddd.domain.model._cotutelle import Cotutelle
from parcours_doctoral.ddd.domain.model._formation import FormationIdentity
from parcours_doctoral.ddd.domain.model._institut import InstitutIdentity
from parcours_doctoral.ddd.domain.model._projet import Projet
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoral, ParcoursDoctoralIdentity
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from osis_common.ddd import interface


class ParcoursDoctoralService(interface.DomainService):
    @classmethod
    def initier(cls, proposition: 'Proposition', groupe_de_supervision: 'GroupeDeSupervision') -> ParcoursDoctoral:
        entity_id = ParcoursDoctoralIdentity(uuid=proposition.entity_id.uuid)

        # TODO duplicate uploaded files

        # TODO duplicate promoters / students roles

        return ParcoursDoctoral(
            entity_id=entity_id,
            statut=ChoixStatutParcoursDoctoral.ADMITTED,
            formation_id=FormationIdentity(sigle=proposition.sigle_formation, annee=proposition.annee),
            matricule_doctorant=proposition.matricule_candidat,
            cotutelle=Cotutelle(
                motivation=groupe_de_supervision.cotutelle.motivation,
                institution_fwb=groupe_de_supervision.cotutelle.institution_fwb,
                institution=groupe_de_supervision.cotutelle.institution,
                autre_institution_nom=groupe_de_supervision.cotutelle.autre_institution_nom,
                autre_institution_adresse=groupe_de_supervision.cotutelle.autre_institution_adresse,
                demande_ouverture=groupe_de_supervision.cotutelle.demande_ouverture,
                convention=groupe_de_supervision.cotutelle.convention,
                autres_documents=groupe_de_supervision.cotutelle.autres_documents,
            ),
            projet=Projet(
                titre=proposition.projet.titre,
                resume=proposition.projet.resume,
                documents=proposition.projet.documents,
                langue_redaction_these=proposition.projet.langue_redaction_these,
                institut_these=proposition.projet.institut_these,
                lieu_these=proposition.projet.lieu_these,
                deja_commence=proposition.projet.deja_commence,
                deja_commence_institution=proposition.projet.deja_commence_institution,
                date_debut=proposition.projet.date_debut,
                graphe_gantt=proposition.projet.graphe_gantt,
                proposition_programme_doctoral=proposition.projet.proposition_programme_doctoral,
                projet_formation_complementaire=proposition.projet.projet_formation_complementaire,
                lettres_recommandation=proposition.projet.lettres_recommandation,
            ),
            # Financing
            # TODO
        )
