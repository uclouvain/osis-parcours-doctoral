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
import json

from django.views.generic import TemplateView
from osis_comment.contrib.mixins import CommentEntryAPIMixin
from rest_framework.exceptions import PermissionDenied

from backoffice.settings.base import CKEDITOR_CONFIGS
from parcours_doctoral.api.permissions import DoctorateAPIPermissionRequiredMixin
from parcours_doctoral.constants import COMMENT_TAB_GLOBAL
from parcours_doctoral.views.mixins import ParcoursDoctoralViewMixin

__namespace__ = False

__all__ = [
    'CommentsView',
    'CommentApiView',
]


class CommentsView(ParcoursDoctoralViewMixin, TemplateView):
    urlpatterns = 'comments'
    permission_required = 'parcours_doctoral.view_comments'
    template_name = 'parcours_doctoral/details/comments.html'

    extra_context = {
        'COMMENT_TAB_GLOBAL': COMMENT_TAB_GLOBAL,
        'ckeditor_config': json.dumps(CKEDITOR_CONFIGS['minimal']),
    }


class CommentApiView(DoctorateAPIPermissionRequiredMixin, CommentEntryAPIMixin):
    urlpatterns = {
        'comments-api': ['comments-api', f'comments-api/<uuid:comment_uuid>'],
    }

    permission_mapping = {
        'GET': 'parcours_doctoral.view_comments',
        'POST': 'parcours_doctoral.change_comments',
        'PUT': 'parcours_doctoral.change_comments',
        'PATCH': 'parcours_doctoral.change_comments',
        'DELETE': 'parcours_doctoral.change_comments',
    }

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)

        additional_permission_method = {
            'PUT': self.has_change_permission,
            'DELETE': self.has_delete_permission,
        }.get(self.request.method)

        if additional_permission_method and not additional_permission_method(obj):
            raise PermissionDenied

    def has_change_permission(self, comment):
        return comment.author == getattr(self.request.user, 'person', None)

    def has_delete_permission(self, comment):
        return comment.author == getattr(self.request.user, 'person', None)
