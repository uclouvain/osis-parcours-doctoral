# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

__all__ = [
    "PARCOURS_DOCTORAL_EMAIL_SIGNATURE_STUDENT",
    "PARCOURS_DOCTORAL_EMAIL_SIGNATURE_REFUSAL",
    "PARCOURS_DOCTORAL_EMAIL_SIGNATURE_REQUESTS_ACTOR",
    "PARCOURS_DOCTORAL_EMAIL_SIGNATURE_REQUESTS_STUDENT",
    "PARCOURS_DOCTORAL_EMAIL_MEMBER_REMOVED",
]

from parcours_doctoral.mail_templates import PARCOURS_DOCTORAL_TAG
from parcours_doctoral.mail_templates.tokens import common_tokens

PARCOURS_DOCTORAL_EMAIL_SIGNATURE_REQUESTS_STUDENT = 'osis-parcours-doctoral-signature-requests-student'
templates.register(
    PARCOURS_DOCTORAL_EMAIL_SIGNATURE_REQUESTS_STUDENT,
    description=_("Mail sent to the student to confirm supervision group signature requests are sent"),
    tokens=(
        common_tokens
        + [
            Token(
                name='actors_as_list_items',
                description=_("Actors as list items"),
                example="Jean</li><li>Eudes",
            ),
            Token(
                name='actors_comma_separated',
                description=_("Actors, comma-separated"),
                example="Jean, Eudes",
            ),
        ]
    ),
    tag=PARCOURS_DOCTORAL_TAG,
)

signataire_tokens = [
    Token(
        name='signataire_first_name',
        description=_("The first name of the signing actor"),
        example="Jim",
    ),
    Token(
        name='signataire_last_name',
        description=_("The last name of the signing actor"),
        example="Halpert",
    ),
    Token(
        name='signataire_role',
        description=_("Role of the signing actor"),
        example="promoteur",
    ),
    Token(
        name='parcours_doctoral_link_front_supervision',
        description=_("Link to the doctorate supervisory panel (front-office)"),
        example="http://dev.studies.uclouvain.be/somewhere/some-uuid/supervision",
    ),
]

PARCOURS_DOCTORAL_EMAIL_SIGNATURE_REQUESTS_ACTOR = 'osis-parcours-doctoral-signature-requests-actor'
templates.register(
    PARCOURS_DOCTORAL_EMAIL_SIGNATURE_REQUESTS_ACTOR,
    description=_("Mail sent to each actor of the supervision group to request a signature"),
    tokens=common_tokens + signataire_tokens,
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_SIGNATURE_STUDENT = 'osis-parcours-doctoral-signature-student'
templates.register(
    PARCOURS_DOCTORAL_EMAIL_SIGNATURE_STUDENT,
    description=_("Mail sent to the applicant following approval or rejection by a member of the supervisory group"),
    tokens=(
        common_tokens
        + signataire_tokens
        + [
            Token(
                name='decision',
                description=_("The decision of the signing actor"),
                example="Approved",
            ),
            Token(
                name='comment',
                description=_("The public comment about the approval/refusal"),
                example="I would be glad to supervise you",
            ),
            Token(
                name='reason',
                description=_("The reason for refusal"),
                example="I do not handle this kind of doctorates",
            ),
        ]
    ),
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_SIGNATURE_REFUSAL = 'osis-parcours-doctoral-signature-refusal'
templates.register(
    PARCOURS_DOCTORAL_EMAIL_SIGNATURE_REFUSAL,
    description=_("Mail sent to promoters when a member of the supervision panel refuses"),
    tokens=(
        common_tokens
        + signataire_tokens
        + [
            Token(
                name='decision',
                description=_("The decision of the signing actor"),
                example="Approved",
            ),
            Token(
                name='comment',
                description=_("The public comment about the approval/refusal"),
                example="I would be glad to supervise you",
            ),
            Token(
                name='reason',
                description=_("The reason for refusal"),
                example="I do not handle this kind of doctorates",
            ),
            Token(
                name='actor_first_name',
                description=_("The first name of the recipient"),
                example="Jane",
            ),
            Token(
                name='actor_last_name',
                description=_("The last name of the recipient"),
                example="Smith",
            ),
        ]
    ),
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_MEMBER_REMOVED = 'osis-parcours-doctoral-member-removed'
templates.register(
    PARCOURS_DOCTORAL_EMAIL_MEMBER_REMOVED,
    description=_("Mail sent to the member of the supervision panel when deleted by the student"),
    tokens=common_tokens
    + [
        Token(
            name='actor_first_name',
            description=_("The first name of the recipient"),
            example="Jane",
        ),
        Token(
            name='actor_last_name',
            description=_("The last name of the recipient"),
            example="Smith",
        ),
    ],
    tag=PARCOURS_DOCTORAL_TAG,
)
