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

from .envoyer_message_au_doctorant_service import envoyer_message_au_doctorant
from .initialiser_document_service import initialiser_document
from .initialiser_parcours_doctoral import initialiser_parcours_doctoral
from .modifier_cotutelle_service import modifier_cotutelle
from .modifier_financement_service import modifier_financement
from .modifier_projet_service import modifier_projet
from .modifier_document_service import modifier_document
from .supprimer_document_service import supprimer_document

__all__ = [
    "envoyer_message_au_doctorant",
    "initialiser_document",
    "initialiser_parcours_doctoral",
    "modifier_cotutelle",
    "modifier_financement",
    "modifier_projet",
    "modifier_document",
    "supprimer_document",
]
