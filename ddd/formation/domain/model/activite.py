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
import decimal
from typing import Optional

import attr

from osis_common.ddd import interface
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.formation.domain.model.enums import (
    CategorieActivite,
    ContexteFormation,
    StatutActivite,
)
from parcours_doctoral.ddd.formation.domain.validator.validator_by_business_action import (
    RefusActiviteValidationList,
    RevenirASoumiseActiviteValidationList,
)


@attr.dataclass(frozen=True, slots=True)
class ActiviteIdentity(interface.EntityIdentity):
    uuid: str


@attr.dataclass(slots=True, hash=False, eq=False)
class Activite(interface.RootEntity):
    entity_id: 'ActiviteIdentity'
    parcours_doctoral_id: 'ParcoursDoctoralIdentity'
    categorie: 'CategorieActivite'
    contexte: 'ContexteFormation'
    statut: 'StatutActivite' = StatutActivite.NON_SOUMISE
    ects: Optional[float] = None
    cours_complete: bool = False

    parent_id: Optional['ActiviteIdentity'] = None
    categorie_parente: Optional['CategorieActivite'] = None

    avis_promoteur_reference: Optional[bool] = None
    commentaire_promoteur_reference: str = ''
    commentaire_gestionnaire: str = ''

    def soumettre(self):
        self.statut = StatutActivite.SOUMISE

    def accepter(self):
        self.statut = StatutActivite.ACCEPTEE

    def revenir_a_soumise(self):
        RevenirASoumiseActiviteValidationList(self).validate()
        self.statut = StatutActivite.SOUMISE

    def refuser(self, avec_modification: bool, remarque: str):
        RefusActiviteValidationList(self, remarque).validate()
        if avec_modification:
            self.statut = StatutActivite.NON_SOUMISE
        else:
            self.statut = StatutActivite.REFUSEE
        if self.categorie_parente != CategorieActivite.SEMINAR:
            self.commentaire_gestionnaire = remarque

    def donner_avis_promoteur_reference(self, approbation, commentaire):
        self.avis_promoteur_reference = approbation
        self.commentaire_promoteur_reference = commentaire

    def encoder_note_cours_ucl(self, note: str):
        try:
            if decimal.Decimal(note) >= 10:
                self.cours_complete = True
        except decimal.InvalidOperation:
            pass
