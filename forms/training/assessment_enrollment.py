# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from django import forms
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy

from base.forms.utils import EMPTY_CHOICE
from base.forms.utils.autocomplete import ListSelect2
from deliberation.models.enums.numero_session import Session
from parcours_doctoral.models import Activity


class AssessmentEnrollmentForm(forms.Form):
    course = forms.ChoiceField(
        label=gettext_lazy('Learning unit'),
        widget=ListSelect2,
    )

    session = forms.ChoiceField(
        choices=EMPTY_CHOICE + Session.choices(),
        label=gettext_lazy('Session'),
    )

    late_enrollment = forms.BooleanField(
        label=gettext_lazy('Late enrollment'),
        required=False,
    )

    def __init__(self, courses: QuerySet[Activity], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['course'].choices = EMPTY_CHOICE + tuple(
            (str(course.uuid), f'{course.learning_year_acronym} - {course.learning_year_title}') for course in courses
        )

        if self.initial:
            self.fields['course'].disabled = True
