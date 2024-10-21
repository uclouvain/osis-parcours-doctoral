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
    "PARCOURS_DOCTORAL_EMAIL_STUDENT_DOCTORAL_TRAINING_NEEDS_UPDATE",
    "PARCOURS_DOCTORAL_EMAIL_STUDENT_DOCTORAL_TRAINING_REFUSED",
    "PARCOURS_DOCTORAL_EMAIL_REFERENCE_PROMOTER_DOCTORAL_TRAININGS_SUBMITTED",
    "PARCOURS_DOCTORAL_EMAIL_STUDENT_COMPLEMENTARY_TRAINING_NEEDS_UPDATE",
    "PARCOURS_DOCTORAL_EMAIL_STUDENT_COMPLEMENTARY_TRAINING_REFUSED",
    "PARCOURS_DOCTORAL_EMAIL_REFERENCE_PROMOTER_COMPLEMENTARY_TRAININGS_SUBMITTED",
    "PARCOURS_DOCTORAL_EMAIL_STUDENT_COURSE_ENROLLMENT_NEEDS_UPDATE",
    "PARCOURS_DOCTORAL_EMAIL_STUDENT_COURSE_ENROLLMENT_REFUSED",
    "PARCOURS_DOCTORAL_EMAIL_REFERENCE_PROMOTER_COURSE_ENROLLMENTS_SUBMITTED",
]


training_common_tokens = common_tokens + [
    Token(
        name='parcours_doctoral_link_back_doctoral_training',
        description=_("Link to the doctoral training panel (back-office)"),
        example="http://dev.osis.uclouvain.be/somewhere/some-uuid/doctoral-training",
    ),
]

# PhD training
doctoral_training_token = [
    Token(
        name='parcours_doctoral_link_front_doctoral_training',
        description=_("Link to the doctoral training panel (front-office)"),
        example="http://dev.studies.uclouvain.be/somewhere/some-uuid/doctoral-training",
    ),
]
PARCOURS_DOCTORAL_EMAIL_REFERENCE_PROMOTER_DOCTORAL_TRAININGS_SUBMITTED = (
    'osis-parcours-doctoral-doctoral-training-submitted-reference-promoter'
)
templates.register(
    PARCOURS_DOCTORAL_EMAIL_REFERENCE_PROMOTER_DOCTORAL_TRAININGS_SUBMITTED,
    description=_("Mail sent to reference promoter to inform of the submission of doctoral training activities"),
    tokens=training_common_tokens + doctoral_training_token,
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_STUDENT_DOCTORAL_TRAINING_REFUSED = 'osis-parcours-doctoral-doctoral-training-refused-student'
templates.register(
    PARCOURS_DOCTORAL_EMAIL_STUDENT_DOCTORAL_TRAINING_REFUSED,
    description=_("Mail sent to the student to inform of the refusal of doctoral training activity"),
    tokens=(
        training_common_tokens
        + doctoral_training_token
        + [
            Token(
                name='reason',
                description=_("The reason for refusal"),
                example="This activity is not part of doctoral program",
            ),
            Token(
                name='activity_title',
                description=_("The activity title"),
                example="Cours de langue : Anglais médiéval (ANGMED003) - 2 ECTS",
            ),
        ]
    ),
    tag=PARCOURS_DOCTORAL_TAG,
)
PARCOURS_DOCTORAL_EMAIL_STUDENT_DOCTORAL_TRAINING_NEEDS_UPDATE = (
    'osis-parcours-doctoral-doctoral-training-needs-update-student'
)
templates.register(
    PARCOURS_DOCTORAL_EMAIL_STUDENT_DOCTORAL_TRAINING_NEEDS_UPDATE,
    description=_("Mail sent to the student to update a doctoral training activity"),
    tokens=(
        training_common_tokens
        + doctoral_training_token
        + [
            Token(
                name='reason',
                description=_("The reason for needing update"),
                example="Some information is missing",
            ),
            Token(
                name='activity_title',
                description=_("The activity title"),
                example="Cours de langue : Anglais médiéval (ANGMED003) - 2 ECTS",
            ),
        ]
    ),
    tag=PARCOURS_DOCTORAL_TAG,
)

# Complementary training
complementary_training_token = [
    Token(
        name='parcours_doctoral_link_front_complementary_training',
        description=_("Link to the complementary training panel (front-office)"),
        example="http://dev.studies.uclouvain.be/somewhere/some-uuid/complementary-training",
    ),
]
PARCOURS_DOCTORAL_EMAIL_REFERENCE_PROMOTER_COMPLEMENTARY_TRAININGS_SUBMITTED = (
    'osis-parcours-doctoral-complementary-training-submitted-reference-promoter'
)
templates.register(
    PARCOURS_DOCTORAL_EMAIL_REFERENCE_PROMOTER_COMPLEMENTARY_TRAININGS_SUBMITTED,
    description=_("Mail sent to reference promoter to inform of the submission of complementary training activities"),
    tokens=training_common_tokens + complementary_training_token,
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_STUDENT_COMPLEMENTARY_TRAINING_REFUSED = (
    'osis-parcours-doctoral-complementary-training-refused-student'
)
templates.register(
    PARCOURS_DOCTORAL_EMAIL_STUDENT_COMPLEMENTARY_TRAINING_REFUSED,
    description=_("Mail sent to the student to inform of the refusal of complementary training activity"),
    tokens=training_common_tokens
    + complementary_training_token
    + [
        Token(
            name='reason',
            description=_("The reason for refusal"),
            example="This activity is not part of complementary program",
        ),
        Token(
            name='activity_title',
            description=_("The activity title"),
            example="Cours de langue : Anglais médiéval (ANGMED003) - 2 ECTS",
        ),
    ],
    tag=PARCOURS_DOCTORAL_TAG,
)
PARCOURS_DOCTORAL_EMAIL_STUDENT_COMPLEMENTARY_TRAINING_NEEDS_UPDATE = (
    'osis-parcours-doctoral-complementary-training-needs-update-student'
)
templates.register(
    PARCOURS_DOCTORAL_EMAIL_STUDENT_COMPLEMENTARY_TRAINING_NEEDS_UPDATE,
    description=_("Mail sent to the student to update a complementary training activity"),
    tokens=(
        training_common_tokens
        + complementary_training_token
        + [
            Token(
                name='reason',
                description=_("The reason for needing update"),
                example="Some information is missing",
            ),
            Token(
                name='activity_title',
                description=_("The activity title"),
                example="Cours de langue : Anglais médiéval (ANGMED003) - 2 ECTS",
            ),
        ]
    ),
    tag=PARCOURS_DOCTORAL_TAG,
)

# Course enrollment
course_enrollment_token = [
    Token(
        name='parcours_doctoral_link_front_course_enrollment',
        description=_("Link to the doctoral training panel (front-office)"),
        example="http://dev.studies.uclouvain.be/somewhere/some-uuid/course-enrollment",
    ),
]
PARCOURS_DOCTORAL_EMAIL_REFERENCE_PROMOTER_COURSE_ENROLLMENTS_SUBMITTED = (
    'osis-parcours-doctoral-course-enrollment-submitted-reference-promoter'
)
templates.register(
    PARCOURS_DOCTORAL_EMAIL_REFERENCE_PROMOTER_COURSE_ENROLLMENTS_SUBMITTED,
    description=_("Mail sent to reference promoter to inform of the submission of course enrollment"),
    tokens=training_common_tokens + course_enrollment_token,
    tag=PARCOURS_DOCTORAL_TAG,
)

PARCOURS_DOCTORAL_EMAIL_STUDENT_COURSE_ENROLLMENT_REFUSED = 'osis-parcours-doctoral-course-enrollment-refused-student'
templates.register(
    PARCOURS_DOCTORAL_EMAIL_STUDENT_COURSE_ENROLLMENT_REFUSED,
    description=_("Mail sent to the student to inform of the refusal of course enrollment"),
    tokens=(
        training_common_tokens
        + course_enrollment_token
        + [
            Token(
                name='reason',
                description=_("The reason for refusal"),
                example="This activity is not part of doctoral program",
            ),
            Token(
                name='activity_title',
                description=_("The activity title"),
                example="Business Process Management - 2023-24 - Formation doctorale - 10 ECTS",
            ),
        ]
    ),
    tag=PARCOURS_DOCTORAL_TAG,
)
PARCOURS_DOCTORAL_EMAIL_STUDENT_COURSE_ENROLLMENT_NEEDS_UPDATE = (
    'osis-parcours-doctoral-course-enrollment-needs-update-student'
)
templates.register(
    PARCOURS_DOCTORAL_EMAIL_STUDENT_COURSE_ENROLLMENT_NEEDS_UPDATE,
    description=_("Mail sent to the student to update a course enrollment"),
    tokens=(
        training_common_tokens
        + course_enrollment_token
        + [
            Token(
                name='reason',
                description=_("The reason for needing update"),
                example="Some information is missing",
            ),
            Token(
                name='activity_title',
                description=_("The activity title"),
                example="Business Process Management - 2023-24 - Formation doctorale - 10 ECTS",
            ),
        ]
    ),
    tag=PARCOURS_DOCTORAL_TAG,
)
