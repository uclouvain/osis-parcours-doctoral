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
from .completer_epreuve_confirmation_par_promoteur_service import (
    completer_epreuve_confirmation_par_promoteur,
)
from .confirmer_echec_service import confirmer_echec
from .confirmer_repassage_service import confirmer_repassage
from .confirmer_reussite_service import confirmer_reussite
from .modifier_epreuve_confirmation_par_cdd_service import (
    modifier_epreuve_confirmation_par_cdd,
)
from .soumettre_avis_prolongation_service import soumettre_avis_prolongation
from .soumettre_epreuve_confirmation_service import soumettre_epreuve_confirmation
from .soumettre_report_de_date_service import soumettre_report_de_date
from .soumettre_report_de_date_par_cdd_service import soumettre_report_de_date_par_cdd
from .televerser_avis_renouvellement_mandat_recherche_service import (
    televerser_avis_renouvellement_mandat_recherche,
)
