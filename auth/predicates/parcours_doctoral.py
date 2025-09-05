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
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from rules import predicate

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixTypeAdmission,
)
from osis_role.errors import predicate_failed_msg
from parcours_doctoral.ddd.domain.model.enums import (
    STATUTS_DOCTORAT_DEFENSE_PRIVEE_EN_COURS,
    STATUTS_DOCTORAT_EPREUVE_CONFIRMATION_EN_COURS,
    ChoixStatutParcoursDoctoral,
)
from parcours_doctoral.models import ActorType
from parcours_doctoral.models.parcours_doctoral import ParcoursDoctoral


def _build_queryset_cache_key_from_role_qs(role_qs, suffix):
    """
    Return a cache key based on the model class of the queryset. This is useful when we want to cache a queryset for a
    user who has several roles.
    :param role_qs: The role queryset
    :param suffix: The suffix of the cache key
    :return: The cache key
    """
    return f'{role_qs.model.__module__}_{role_qs.model.__name__}_{suffix}'.replace('.', '_')


@predicate(bind=True)
@predicate_failed_msg(message=_("The doctorate hasn't got a valid enrolment"))
def has_valid_enrollment(self, user: User, obj: ParcoursDoctoral):
    cache_key = f'admission_{obj.pk}_has_valid_enrollment'
    if not hasattr(user, cache_key):
        setattr(user, cache_key, obj.has_valid_enrollment)
    return getattr(user, cache_key)


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be the request author to access this doctoral training"))
def is_parcours_doctoral_student(self, user: User, obj: ParcoursDoctoral):
    return obj.student == user.person and has_valid_enrollment(user, obj)


@predicate(bind=True)
@predicate_failed_msg(message=_("The doctorate is not initialized"))
def is_related_to_an_admission(self, user: User, obj: ParcoursDoctoral):
    return obj.admission.type == ChoixTypeAdmission.ADMISSION.name


@predicate(bind=True)
@predicate_failed_msg(message=_("The jury is not in progress"))
def is_jury_in_progress(self, user: User, obj: ParcoursDoctoral):
    return obj.status in {
        ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE.name,
        ChoixStatutParcoursDoctoral.JURY_REFUSE_CDD.name,
        ChoixStatutParcoursDoctoral.JURY_REFUSE_ADRE.name,
    }


@predicate(bind=True)
@predicate_failed_msg(message=_("The jury signing is not in progress"))
def is_jury_signing_in_progress(self, user: User, obj: ParcoursDoctoral):
    return obj.status == ChoixStatutParcoursDoctoral.JURY_SOUMIS.name


@predicate(bind=True)
@predicate_failed_msg(message=_("The jury signing is not in progress"))
def is_jury_approuve_ca(self, user: User, obj: ParcoursDoctoral):
    return obj.status == ChoixStatutParcoursDoctoral.JURY_APPROUVE_CA.name


@predicate(bind=True)
@predicate_failed_msg(message=_("The jury signing is not in progress"))
def is_jury_approuve_cdd(self, user: User, obj: ParcoursDoctoral):
    return obj.status == ChoixStatutParcoursDoctoral.JURY_APPROUVE_CDD.name


@predicate(bind=True)
@predicate_failed_msg(message=_("The confirmation paper is not in progress"))
def submitted_confirmation_paper(self, user: User, obj: ParcoursDoctoral):
    return obj.status == ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name


@predicate(bind=True)
@predicate_failed_msg(
    message=_("The doctorate must be in the status '%(status)s' to realize this action.")
    % {
        'status': ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE.value,
    }
)
def private_defense_is_submitted(self, user: User, obj: ParcoursDoctoral):
    return obj.status == ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE.name


@predicate(bind=True)
@predicate_failed_msg(message=_("The confirmation paper is not in progress"))
def confirmation_paper_in_progress(self, user: User, obj: ParcoursDoctoral):
    return obj.status in STATUTS_DOCTORAT_EPREUVE_CONFIRMATION_EN_COURS


@predicate(bind=True)
@predicate_failed_msg(message=_("The private defense is not in progress"))
def private_defense_in_progress(self, user: User, obj: ParcoursDoctoral):
    return obj.status in STATUTS_DOCTORAT_DEFENSE_PRIVEE_EN_COURS


@predicate(bind=True)
@predicate_failed_msg(message=_("Complementary training not enabled"))
def complementary_training_enabled(self, user: User, obj: ParcoursDoctoral):
    return (
        hasattr(obj.training.management_entity, 'doctorate_config')
        and obj.training.management_entity.doctorate_config.is_complementary_training_enabled
    )


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be a member of the doctoral commission to access this doctoral training"))
def is_part_of_doctoral_commission(self, user: User, obj: ParcoursDoctoral):
    return (
        isinstance(obj, ParcoursDoctoral)
        and obj.training.management_entity_id in self.context['role_qs'].get_entities_ids()
    )


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be the request supervisor to access this doctoral training"))
def is_parcours_doctoral_promoter(self, user: User, obj: ParcoursDoctoral):
    return (
        has_valid_enrollment(user, obj)
        and obj.supervision_group
        and user.person.pk
        in [
            actor.person_id
            for actor in obj.supervision_group.actors.all()
            if actor.parcoursdoctoralsupervisionactor.type == ActorType.PROMOTER.name
        ]
    )


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be the contact supervisor to access this doctoral training"))
def is_parcours_doctoral_reference_promoter(self, user: User, obj: ParcoursDoctoral):
    return (
        has_valid_enrollment(user, obj)
        and obj.supervision_group
        and user.person.pk
        in [
            actor.person_id
            for actor in obj.supervision_group.actors.all()
            if actor.parcoursdoctoralsupervisionactor.type == ActorType.PROMOTER.name
            and actor.parcoursdoctoralsupervisionactor.is_reference_promoter
        ]
    )


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be a member of the committee to access this doctoral training"))
def is_part_of_committee(self, user: User, obj: ParcoursDoctoral):
    return (
        obj.has_valid_enrollment
        and obj.supervision_group
        and user.person.pk in [actor.person_id for actor in obj.supervision_group.actors.all()]
    )


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be a member of the jury to access this doctoral training"))
def is_part_of_jury(self, user: User, obj: ParcoursDoctoral):
    return user.person.pk in [actor.person_id for actor in obj.jury_group.actors.all()]


@predicate(bind=True)
def is_part_of_education_group(self, user: User, obj: ParcoursDoctoral):
    cache_key = _build_queryset_cache_key_from_role_qs(self.context['role_qs'], 'education_groups_affected')

    if not hasattr(user, cache_key):
        setattr(user, cache_key, self.context['role_qs'].get_education_groups_affected())

    return obj.training.education_group_id in getattr(user, cache_key)
