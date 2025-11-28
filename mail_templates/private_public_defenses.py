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
    'PARCOURS_DOCTORAL_EMAIL_PRIVATE_PUBLIC_DEFENSES_AUTHORISATION',
    'PARCOURS_DOCTORAL_EMAIL_PRIVATE_PUBLIC_DEFENSES_JURY_INVITATION',
    'PARCOURS_DOCTORAL_EMAIL_PRIVATE_PUBLIC_DEFENSES_ON_SUCCESS',
]


private_public_defenses_tokens = common_tokens + [
    Token(
        name='management_entity_name',
        description=_('Name of the management entity'),
        example='Faculté des sciences économiques, sociales, politiques et de communication',
    ),
    Token(
        name='sender_name',
        description=_('Name of the manager sending the email'),
        example='John Doe',
    ),
]

PARCOURS_DOCTORAL_EMAIL_PRIVATE_PUBLIC_DEFENSES_AUTHORISATION = (
    'osis-parcours-doctoral-private-public-defenses-authorisation'
)
templates.register(
    PARCOURS_DOCTORAL_EMAIL_PRIVATE_PUBLIC_DEFENSES_AUTHORISATION,
    description=_(
        'Mail sent to the doctoral student to inform of the authorisation of the private and the public defences'
    ),
    tokens=private_public_defenses_tokens
    + [
        Token(
            name='private_defense_date',
            description=_('Date of the private defence (DD/MM/YYYY)'),
            example='01/04/2022',
        ),
        Token(
            name='public_defense_date',
            description=_('Date of the public defence (DD/MM/YYYY)'),
            example='01/04/2022',
        ),
    ],
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_PRIVATE_PUBLIC_DEFENSES_JURY_INVITATION = (
    'osis-parcours-doctoral-private-public-defenses-jury-invitation'
)
templates.register(
    PARCOURS_DOCTORAL_EMAIL_PRIVATE_PUBLIC_DEFENSES_JURY_INVITATION,
    description=_('Mail sent to the jury members to invite them to the private and the public defences'),
    tokens=private_public_defenses_tokens
    + [
        Token(
            name='private_defense_date',
            description=_('Date of the private defence (DD/MM/YYYY)'),
            example='01/04/2022',
        ),
        Token(
            name='private_defense_place',
            description=_('Place of the private defence'),
            example='B1',
        ),
        Token(
            name='public_defense_date',
            description=_('Date of the public defence (DD/MM/YYYY)'),
            example='01/04/2022',
        ),
        Token(
            name='public_defense_place',
            description=_('Place of the public defence'),
            example='B1',
        ),
        Token(
            name='deliberation_room',
            description=_('Deliberation room'),
            example='R1',
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

PARCOURS_DOCTORAL_EMAIL_PRIVATE_PUBLIC_DEFENSES_ON_SUCCESS = 'osis-parcours-doctoral-private-public-defenses-on-success'
templates.register(
    PARCOURS_DOCTORAL_EMAIL_PRIVATE_PUBLIC_DEFENSES_ON_SUCCESS,
    description=_(
        'Mail sent to the doctoral student to inform him of the favourable opinion on the private and public defences'
    ),
    tokens=private_public_defenses_tokens
    + [
        Token(
            name='parcours_doctoral_link_front_public_defense_minutes',
            description=_('The link to the public defence minutes'),
            example='http://dev.studies.uclouvain.be/parcours_doctoral/.../public-defense',
        ),
    ],
    tag=PARCOURS_DOCTORAL_TAG,
)
