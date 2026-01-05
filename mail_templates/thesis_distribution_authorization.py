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
    'PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_PROMOTER_INVITATION',
    'PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_PROMOTER_INVITATION_CONFIRMATION',
    'PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_PROMOTER_REFUSAL',
    'PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_PROMOTER_APPROVAL',
    'PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_ADRE_REFUSAL',
    'PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_ADRE_APPROVAL',
    'PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_SCEB_REFUSAL',
]


PROMOTER_NAME_TOKEN = Token(
    name='promoter_name',
    description=_('The name of the supervisor'),
    example='John Doe',
)

PROMOTER_TITLE_TOKEN = Token(
    name='promoter_title_uppercase',
    description=_('The title of the supervisor'),
    example='The professor',
)

PROMOTER_TITLE_LOWERCASE_TOKEN = Token(
    name='promoter_title_lowercase',
    description=_('The title of the supervisor (in lowercase)'),
    example='the professor',
)

CDD_MANAGERS_NAMES_TOKEN = Token(
    name='cdd_manager_names',
    description=_('Names of the CDD managers'),
    example='John Doe, Jane Doe',
)

DOCTORAL_COMMISSION_TOKEN = Token(
    name='doctoral_commission',
    description=_('Name of the doctoral commission'),
    example='Doctoral Commission',
)

PROMOTER_REFUSAL_REASON_TOKEN = Token(
    name='promoter_refusal_reason',
    description=_('Refusal reason of the supervisor'),
    example='There is a problem.',
)

ADRE_REFUSAL_REASON_TOKEN = Token(
    name='adre_refusal_reason',
    description=_('Refusal reason of ADRE'),
    example='There is a problem.',
)

SCEB_REFUSAL_REASON_TOKEN = Token(
    name='sceb_refusal_reason',
    description=_('Refusal reason of SCEB'),
    example='There is a problem.',
)

ADRE_MANAGER_NAME_TOKEN = Token(
    name='adre_manager_name',
    description=_('Name of the ADRE manager'),
    example='John Doe',
)

SCEB_MANAGER_NAME_TOKEN = Token(
    name='sceb_manager_name',
    description=_('Name of the SCEB manager'),
    example='John Doe',
)

THESIS_DISTRIBUTION_AUTHORIZATION_FORM_FRONT_LINK_TOKEN = Token(
    name='thesis_distribution_authorization_form_front_link',
    description=_('Link to the thesis distribution authorization form (frontoffice)'),
    example='http://dev.studies.uclouvain.be/parcours_doctoral/.../thesis_distribution_authorization',
)

THESIS_DISTRIBUTION_AUTHORIZATION_FORM_BACK_LINK_TOKEN = Token(
    name='thesis_distribution_authorization_form_back_link',
    description=_('Link to the thesis distribution authorization form (backoffice)'),
    example='http://dev.osis.uclouvain.be/parcours_doctoral/.../thesis_distribution_authorization',
)


DIAL_LINK_TOKEN = Token(
    name='dial_link',
    description=_('DIAL link'),
    example='http://dev.dial.uclouvain.be',
)


PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_PROMOTER_INVITATION = (
    'osis-parcours-doctoral-thesis-distribution-authorization-promoter-invitation'
)
templates.register(
    PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_PROMOTER_INVITATION,
    description=_('Mail sent to the supervisor to invite him to authorize the thesis distribution'),
    tokens=common_tokens
    + [
        PROMOTER_NAME_TOKEN,
        THESIS_DISTRIBUTION_AUTHORIZATION_FORM_FRONT_LINK_TOKEN,
        CDD_MANAGERS_NAMES_TOKEN,
        DOCTORAL_COMMISSION_TOKEN,
    ],
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_PROMOTER_INVITATION_CONFIRMATION = (
    'osis-parcours-doctoral-thesis-distribution-authorization-promoter-invitation-confirmation'
)
templates.register(
    PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_PROMOTER_INVITATION_CONFIRMATION,
    description=_('Mail sent to the student to invite him to upload its thesis after the supervisor invitation'),
    tokens=common_tokens
    + [
        DIAL_LINK_TOKEN,
        CDD_MANAGERS_NAMES_TOKEN,
        DOCTORAL_COMMISSION_TOKEN,
    ],
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_PROMOTER_REFUSAL = (
    'osis-parcours-doctoral-thesis-distribution-authorization-promoter-refusal'
)
templates.register(
    PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_PROMOTER_REFUSAL,
    description=_('Mail sent to the student to inform him the promoter refused the thesis distribution authorization'),
    tokens=common_tokens
    + [
        PROMOTER_TITLE_TOKEN,
        PROMOTER_NAME_TOKEN,
        PROMOTER_REFUSAL_REASON_TOKEN,
        CDD_MANAGERS_NAMES_TOKEN,
        DOCTORAL_COMMISSION_TOKEN,
    ],
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_PROMOTER_APPROVAL = (
    'osis-parcours-doctoral-thesis-distribution-authorization-promoter-approval'
)
templates.register(
    PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_PROMOTER_APPROVAL,
    description=_('Mail sent to ADRE to inform that the promoter approved the thesis distribution authorization'),
    tokens=common_tokens
    + [
        PROMOTER_TITLE_LOWERCASE_TOKEN,
        PROMOTER_NAME_TOKEN,
        CDD_MANAGERS_NAMES_TOKEN,
        DOCTORAL_COMMISSION_TOKEN,
    ],
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_ADRE_REFUSAL = (
    'osis-parcours-doctoral-thesis-distribution-authorization-adre-refusal'
)
templates.register(
    PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_ADRE_REFUSAL,
    description=_('Mail sent to the student to inform him that ADRE refused the thesis distribution authorization'),
    tokens=common_tokens
    + [
        ADRE_REFUSAL_REASON_TOKEN,
        ADRE_MANAGER_NAME_TOKEN,
    ],
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_ADRE_APPROVAL = (
    'osis-parcours-doctoral-thesis-distribution-authorization-adre-approval'
)
templates.register(
    PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_ADRE_APPROVAL,
    description=_('Mail sent to SCEB to inform that ADRE approved the thesis distribution authorization'),
    tokens=common_tokens
    + [
        ADRE_MANAGER_NAME_TOKEN,
    ],
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_SCEB_REFUSAL = (
    'osis-parcours-doctoral-thesis-distribution-authorization-sceb-refusal'
)
templates.register(
    PARCOURS_DOCTORAL_EMAIL_THESIS_DISTRIBUTION_AUTHORIZATION_SCEB_REFUSAL,
    description=_('Mail sent to the student to inform him that SCEB refused the thesis distribution authorization'),
    tokens=common_tokens
    + [
        SCEB_REFUSAL_REASON_TOKEN,
        SCEB_MANAGER_NAME_TOKEN,
    ],
    tag=PARCOURS_DOCTORAL_TAG,
)
