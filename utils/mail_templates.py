# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from admission.mail_templates import ADMISSION_EMAIL_GENERIC_ONCE_ADMITTED
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.mail_templates.confirmation_paper import PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT
from parcours_doctoral.models import ParcoursDoctoral


def get_mail_templates_from_doctorate(doctorate: ParcoursDoctoral):
    allowed_templates = [ADMISSION_EMAIL_GENERIC_ONCE_ADMITTED]
    if doctorate.status == ChoixStatutParcoursDoctoral.SUBMITTED_CONFIRMATION.name:
        allowed_templates.append(PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT)
    return allowed_templates
