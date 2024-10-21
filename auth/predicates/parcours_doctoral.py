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
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from rules import predicate

from osis_role.cache import predicate_cache
from osis_role.errors import predicate_failed_msg
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral, STATUTS_DOCTORAT_EPREUVE_CONFIRMATION_EN_COURS
from parcours_doctoral.models.parcours_doctoral import ParcoursDoctoral


@predicate(bind=True)
@predicate_failed_msg(message=_("The jury is not in progress"))
def is_jury_in_progress(self, user: User, obj: ParcoursDoctoral):
    return obj.post_enrolment_status == ChoixStatutParcoursDoctoral.PASSED_CONFIRMATION.name


@predicate(bind=True)
@predicate_failed_msg(message=_("The confirmation paper is not in progress"))
def submitted_confirmation_paper(self, user: User, obj: ParcoursDoctoral):
    return obj.post_enrolment_status == ChoixStatutParcoursDoctoral.SUBMITTED_CONFIRMATION.name


@predicate(bind=True)
@predicate_failed_msg(message=_("The confirmation paper is not in progress"))
def confirmation_paper_in_progress(self, user: User, obj: ParcoursDoctoral):
    return obj.post_enrolment_status in STATUTS_DOCTORAT_EPREUVE_CONFIRMATION_EN_COURS


@predicate(bind=True)
@predicate_failed_msg(message=_("Complementary training not enabled"))
def complementary_training_enabled(self, user: User, obj: ParcoursDoctoral):
    return (
        hasattr(obj.training.management_entity, 'admission_config')
        and obj.training.management_entity.admission_config.is_complementary_training_enabled
    )


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be a member of the doctoral commission to access this admission"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_part_of_doctoral_commission(self, user: User, obj: ParcoursDoctoral):
    return (
        isinstance(obj, ParcoursDoctoral)
        and obj.training.management_entity_id in self.context['role_qs'].get_entities_ids()
    )
