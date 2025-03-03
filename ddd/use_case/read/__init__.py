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
from .lister_documents_service import lister_documents
from .lister_parcours_doctoraux_doctorant_service import (
    lister_parcours_doctoraux_doctorant,
)
from .lister_parcours_doctoraux_supervises_service import (
    lister_parcours_doctoraux_supervises,
)
from .recuperer_document_service import recuperer_document
from .recuperer_parcours_doctoral_service import recuperer_parcours_doctoral

__all__ = [
    'lister_documents',
    'lister_parcours_doctoraux_doctorant',
    'lister_parcours_doctoraux_supervises',
    'recuperer_document',
    'recuperer_parcours_doctoral',
]
