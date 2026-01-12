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
from django.utils.translation import gettext_lazy as _
from osis_mail_template import Token, templates

from parcours_doctoral.mail_templates import PARCOURS_DOCTORAL_TAG
from parcours_doctoral.mail_templates.tokens import common_tokens

__all__ = [
    'PARCOURS_DOCTORAL_EMAIL_ADMISSIBILITY_JURY_INVITATION',
    'PARCOURS_DOCTORAL_EMAIL_ADMISSIBILITY_ON_SUCCESS',
    'PARCOURS_DOCTORAL_EMAIL_ADMISSIBILITY_ON_REPEAT',
    'PARCOURS_DOCTORAL_EMAIL_ADMISSIBILITY_ON_FAILURE',
    'ADMISSIBILITY_TEMPLATES_IDENTIFIERS',
]


admissibility_tokens = common_tokens + [
    Token(
        name='jury_president',
        description=_('Name of the president of the jury (eventually with the title)'),
        example='Prof. Jane Poe',
    ),
    Token(
        name='jury_secretary',
        description=_('Name of the secretary of the jury (eventually with the title)'),
        example="Prof. John Doe",
    ),
]

PARCOURS_DOCTORAL_EMAIL_ADMISSIBILITY_JURY_INVITATION = 'osis-parcours-doctoral-admissibility-jury-invitation'
templates.register(
    PARCOURS_DOCTORAL_EMAIL_ADMISSIBILITY_JURY_INVITATION,
    description=_('Mail sent to the jury members to invite them to the admissibility'),
    tokens=admissibility_tokens
    + [
        Token(
            name='admissibility_decision_date',
            description=_('Date of the decision of the admissibility (DD/MM/YYYY)'),
            example='01/04/2022',
        ),
        Token(
            name='jury_member_first_name',
            description=_('The first name of the jury member'),
            example='John',
        ),
        Token(
            name='jury_member_last_name',
            description=_('The last name of the jury member'),
            example='Doe',
        ),
    ],
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_ADMISSIBILITY_ON_SUCCESS = 'osis-parcours-doctoral-admissibility-on-success'
templates.register(
    PARCOURS_DOCTORAL_EMAIL_ADMISSIBILITY_ON_SUCCESS,
    description=_('Mail sent to the doctoral student to inform him of the favourable opinion on the admissibility'),
    tokens=admissibility_tokens
    + [
        Token(
            name='parcours_doctoral_link_front_admissibility_minutes',
            description=_('The link to the admissibility minutes'),
            example='http://dev.studies.uclouvain.be/parcours_doctoral/.../admissibility',
        ),
        Token(
            name='parcours_doctoral_link_front_thesis_distribution_authorisation',
            description=_('The link to the thesis distribution authorisation page'),
            example='http://dev.studies.uclouvain.be/parcours_doctoral/.../thesis-distribution-authorisation',
        ),
        Token(
            name='student_reference',
            description=_('The reference to use for the student'),
            example='la doctorante',
        ),
    ],
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_ADMISSIBILITY_ON_REPEAT = 'osis-parcours-doctoral-admissibility-on-repeat'
templates.register(
    PARCOURS_DOCTORAL_EMAIL_ADMISSIBILITY_ON_REPEAT,
    description=_('Mail sent to the doctoral student to inform him of the necessity to repeat the admissibility'),
    tokens=admissibility_tokens
    + [
        Token(
            name='parcours_doctoral_link_front_admissibility_minutes',
            description=_('The link to the admissibility minutes'),
            example='http://dev.studies.uclouvain.be/parcours_doctoral/.../admissibility',
        ),
    ],
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_ADMISSIBILITY_ON_FAILURE = 'osis-parcours-doctoral-admissibility-on-failure'
templates.register(
    PARCOURS_DOCTORAL_EMAIL_ADMISSIBILITY_ON_FAILURE,
    description=_('Mail sent to the doctoral student to inform him of the defavourable opinion on the admissibility'),
    tokens=admissibility_tokens
    + [
        Token(
            name='parcours_doctoral_link_front_admissibility_minutes',
            description=_('The link to the admissibility minutes'),
            example='http://dev.studies.uclouvain.be/parcours_doctoral/.../admissibility',
        ),
        Token(
            name='student_personal_pronoun',
            description=_('The personal pronoun to use for the student'),
            example='elle',
        ),
    ],
    tag=PARCOURS_DOCTORAL_TAG,
)

ADMISSIBILITY_TEMPLATES_IDENTIFIERS = {
    PARCOURS_DOCTORAL_EMAIL_ADMISSIBILITY_JURY_INVITATION,
    PARCOURS_DOCTORAL_EMAIL_ADMISSIBILITY_ON_SUCCESS,
    PARCOURS_DOCTORAL_EMAIL_ADMISSIBILITY_ON_REPEAT,
    PARCOURS_DOCTORAL_EMAIL_ADMISSIBILITY_ON_FAILURE,
}
