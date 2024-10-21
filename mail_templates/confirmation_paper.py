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

from parcours_doctoral.mail_templates import PARCOURS_DOCTORAL_TAG
from parcours_doctoral.mail_templates.tokens import common_tokens

__all__ = [
    "PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT",
    "PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRE",
    "PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRI",
    "PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_STUDENT",
    "PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRE",
    "PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRI",
    "PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_STUDENT",
    "PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRE",
    "PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRI",
    "PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_STUDENT",
    "PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_SUBMISSION_ADRE",
    "CONFIRMATION_PAPER_TEMPLATES_IDENTIFIERS",
]


confirmation_paper_tokens = common_tokens + [
    Token(
        name='confirmation_paper_link_front',
        description=_("Link to the admission confirmation paper panel (front-office)"),
        example="http://dev.studies.uclouvain.be/somewhere/some-uuid/confirmation",
    ),
    Token(
        name='confirmation_paper_link_back',
        description=_("Link to the admission confirmation paper panel (back-office)"),
        example="http://dev.osis.uclouvain.be/somewhere/some-uuid/confirmation",
    ),
    Token(
        name='confirmation_paper_deadline',
        description=_("Deadline of the confirmation paper (DD/MM/YYYY)"),
        example="31/04/2022",
    ),
    Token(
        name='confirmation_paper_date',
        description=_("Date of the confirmation paper (DD/MM/YYYY)"),
        example="01/04/2022",
    ),
    Token(
        name='scholarship_grant_acronym',
        description=_("The acronym of the scholarship grant"),
        example="ARC",
    ),
]

PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_SUBMISSION_ADRE = 'osis-parcours-doctoral-confirmation-submission-adre'
templates.register(
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_SUBMISSION_ADRE,
    description=_("Mail sent to ADRE on first submission of the confirmation paper by the doctoral student"),
    tokens=confirmation_paper_tokens,
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT = 'osis-parcours-doctoral-confirmation-info-student'
templates.register(
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT,
    description=_("Mail sent to the doctoral student to give him some information about the confirmation paper"),
    tokens=confirmation_paper_tokens,
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_STUDENT = 'osis-parcours-doctoral-confirmation-on-success-student'
templates.register(
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_STUDENT,
    description=_(
        "Mail sent to the doctoral student to inform him of the favourable opinion on the confirmation paper"
    ),
    tokens=confirmation_paper_tokens,
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRE = 'osis-parcours-doctoral-confirmation-on-success-adre'
templates.register(
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRE,
    description=_("Mail sent to ADRE to inform him of the favourable opinion on one confirmation paper"),
    tokens=confirmation_paper_tokens,
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRI = 'osis-parcours-doctoral-confirmation-on-success-adri'
templates.register(
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRI,
    description=_("Mail sent to ADRI to inform him of the favourable opinion on one confirmation paper"),
    tokens=confirmation_paper_tokens,
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_STUDENT = 'osis-parcours-doctoral-confirmation-on-failure-student'
templates.register(
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_STUDENT,
    description=_(
        "Mail sent to the doctoral student to inform him of the defavourable opinion on the confirmation paper"
    ),
    tokens=confirmation_paper_tokens,
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRE = 'osis-parcours-doctoral-confirmation-on-failure-adre'
templates.register(
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRE,
    description=_("Mail sent to ADRE to inform him of the defavourable opinion on one confirmation paper"),
    tokens=confirmation_paper_tokens,
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRI = 'osis-parcours-doctoral-confirmation-on-failure-adri'
templates.register(
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRI,
    description=_("Mail sent to ADRI to inform him of the defavourable opinion on one confirmation paper"),
    tokens=confirmation_paper_tokens,
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_STUDENT = (
    'osis-parcours-doctoral-confirmation-on-retaking-student'
)
templates.register(
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_STUDENT,
    description=_("Mail sent to the doctoral student to inform him of the necessity to retake the confirmation paper"),
    tokens=confirmation_paper_tokens,
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRE = 'osis-parcours-doctoral-confirmation-on-retaking-adre'
templates.register(
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRE,
    description=_("Mail sent to ADRE to inform him of the necessity to retake one confirmation paper"),
    tokens=confirmation_paper_tokens,
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRI = 'osis-parcours-doctoral-confirmation-on-retaking-adri'
templates.register(
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRI,
    description=_("Mail sent to ADRI to inform him of the necessity to retake one confirmation paper"),
    tokens=confirmation_paper_tokens,
    tag=PARCOURS_DOCTORAL_TAG,
)

CONFIRMATION_PAPER_TEMPLATES_IDENTIFIERS = {
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_SUBMISSION_ADRE,
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT,
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_STUDENT,
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRE,
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_SUCCESS_ADRI,
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_STUDENT,
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRE,
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_ADRI,
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_STUDENT,
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRE,
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_ADRI,
}
