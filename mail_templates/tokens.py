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
from django.utils.translation import gettext_lazy as _

from osis_mail_template import Token

common_tokens = [
    Token(
        name='training_title',
        description=_("Title of the training"),
        example="Doctorat en sciences de la santé publique",
    ),
    Token(
        name='parcours_doctoral_link_front',
        description=_("Link to the PhD training (front-office)"),
        example="http://dev.studies.uclouvain.be/somewhere",
    ),
    Token(
        name='parcours_doctoral_link_back',
        description=_("Link to the PhD training (back-office)"),
        example="http://dev.osis.uclouvain.be/somewhere",
    ),
    Token(
        name='student_first_name',
        description=_("The first name of the student"),
        example="John",
    ),
    Token(
        name='student_last_name',
        description=_("The last name of the student"),
        example="Doe",
    ),
]

PARCOURS_DOCTORAL_ADMISSION_TAG = 'Parcours doctoral'
