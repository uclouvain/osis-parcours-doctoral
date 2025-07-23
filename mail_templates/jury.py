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

__all__ = [
    # "PARCOURS_DOCTORAL_EMAIL_SIGNATURE_REFUSAL",
    "PARCOURS_DOCTORAL_JURY_EMAIL_SIGNATURE_REQUESTS_PROMOTER",
    "PARCOURS_DOCTORAL_JURY_EMAIL_SIGNATURE_REQUESTS_MEMBER",
]

from parcours_doctoral.mail_templates import PARCOURS_DOCTORAL_TAG
from parcours_doctoral.mail_templates.tokens import common_tokens

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
        name='parcours_doctoral_link_front_jury',
        description=_("Link to the doctorate jury panel (front-office)"),
        example="http://dev.studies.uclouvain.be/somewhere/some-uuid/jury",
    ),
    Token(
        name='cdd_manager_names',
        description=_("Names of the CDD managers"),
        example='John Doe, Jane Doe',
    ),
    Token(
        name='doctoral_commission',
        description=_("Name of the doctoral commission"),
        example="Doctoral Commission",
    ),
]


PARCOURS_DOCTORAL_JURY_EMAIL_SIGNATURE_REQUESTS_PROMOTER = 'osis-parcours-doctoral-jury-signature-requests-promoter'
templates.register(
    PARCOURS_DOCTORAL_JURY_EMAIL_SIGNATURE_REQUESTS_PROMOTER,
    description=_("Mail sent to each promoter of the jury to request a signature"),
    tokens=common_tokens + signataire_tokens,
    tag=PARCOURS_DOCTORAL_TAG,
)


PARCOURS_DOCTORAL_JURY_EMAIL_SIGNATURE_REQUESTS_MEMBER = 'osis-parcours-doctoral-jury-signature-requests-member'
templates.register(
    PARCOURS_DOCTORAL_JURY_EMAIL_SIGNATURE_REQUESTS_MEMBER,
    description=_("Mail sent to each member of the jury and to the auditor to request a signature"),
    tokens=common_tokens + signataire_tokens,
    tag=PARCOURS_DOCTORAL_TAG,
)


PARCOURS_DOCTORAL_JURY_EMAIL_MEMBER_REFUSAL = 'osis-parcours-doctoral-jury-member-refusal'
templates.register(
    PARCOURS_DOCTORAL_JURY_EMAIL_MEMBER_REFUSAL,
    description=_("Mail sent to the student when one of the member refuse the jury"),
    tokens=common_tokens
    + signataire_tokens
    + [
        Token(
            name='refusal_reason',
            description=_("Refusal reason"),
            example="I don't want this jury.",
        ),
    ],
    tag=PARCOURS_DOCTORAL_TAG,
)
