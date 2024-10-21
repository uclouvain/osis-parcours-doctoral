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
from django.urls import path as _path

from parcours_doctoral.api import views


def path(pattern, view, name=None):
    return _path(pattern, view.as_view(), name=getattr(view, 'name', name))


app_name = "parcours_doctoral_api_v1"

urlpatterns = [
    # Dashboard
    path('doctorate/dashboard', views.DashboardApiView),
    # Lists
    path('doctorate/list', views.DoctorateListView),
    path('doctorate/supervised-list', views.SupervisedDoctorateListView),
    # Doctorate data
    path('doctorate/<uuid:uuid>', views.DoctorateAPIView),
    # Project
    path('doctorate/<uuid:uuid>/project', views.ProjectApiView),
    # Funding
    path('doctorate/<uuid:uuid>/funding', views.FundingApiView),
    # Cotutelle
    path('doctorate/<uuid:uuid>/cotutelle', views.CotutelleAPIView),
    # Supervision
    path('doctorate/<uuid:uuid>/supervision', views.SupervisionAPIView),
    path('doctorate/<uuid:uuid>/supervision/external/<token>', views.ExternalDoctorateSupervisionAPIView),
    # Submission confirmation
    path('doctorate/<uuid:uuid>/confirmation', views.ConfirmationAPIView),
    path('doctorate/<uuid:uuid>/confirmation/last', views.LastConfirmationAPIView),
    path('doctorate/<uuid:uuid>/confirmation/last/canvas', views.LastConfirmationCanvasAPIView),
    path('doctorate/<uuid:uuid>/supervised_confirmation', views.SupervisedConfirmationAPIView),
    # Jury
    path('doctorate/<uuid:uuid>/jury/preparation', views.JuryPreparationAPIView),
    path('doctorate/<uuid:uuid>/jury/members', views.JuryMembersListAPIView),
    path('doctorate/<uuid:uuid>/jury/members/<uuid:member_uuid>', views.JuryMemberDetailAPIView),
    # Training
    path('doctorate/<uuid:uuid>/training/config', views.TrainingConfigView),
    path('doctorate/<uuid:uuid>/doctoral-training', views.DoctoralTrainingListView),
    path('doctorate/<uuid:uuid>/training/submit', views.TrainingSubmitView),
    path('doctorate/<uuid:uuid>/training/assent', views.TrainingAssentView),
    path('doctorate/<uuid:uuid>/training/<uuid:activity_id>', views.TrainingView),
    path('doctorate/<uuid:uuid>/complementary-training', views.ComplementaryTrainingListView),
    path('doctorate/<uuid:uuid>/course-enrollment', views.CourseEnrollmentListView),
    # References
    path('references/scholarship/<uuid:uuid>', views.RetrieveScholarshipView),
    # Autocomplete
    path('autocomplete/tutor', views.AutocompleteTutorView),
    path('autocomplete/person', views.AutocompletePersonView),
    path('autocomplete/scholarship', views.AutocompleteScholarshipView),
]
