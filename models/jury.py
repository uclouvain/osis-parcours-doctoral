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
import uuid

from django.db import models
from django.db.models import CheckConstraint, Q
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from parcours_doctoral.ddd.jury.domain.model.enums import (
    GenreMembre,
    RoleJury,
    TitreMembre,
)

__all__ = ['JuryMember']

from parcours_doctoral.models.actor import ActorType


class JuryMember(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )
    role = models.CharField(
        verbose_name=pgettext_lazy('jury', 'Role'),
        choices=RoleJury.choices(),
        max_length=50,
    )
    parcours_doctoral = models.ForeignKey(
        'parcours_doctoral.ParcoursDoctoral',
        verbose_name=_('Doctorate'),
        on_delete=models.CASCADE,
        related_name='jury_members',
    )

    other_institute = models.CharField(
        verbose_name=_('Other institute'),
        max_length=255,
        default='',
        blank=True,
    )

    # Promoter only
    promoter = models.ForeignKey(
        'parcours_doctoral.ParcoursDoctoralSupervisionActor',
        verbose_name=_('Supervisor'),
        on_delete=models.PROTECT,
        limit_choices_to={"type": ActorType.PROMOTER.name},
        null=True,
        blank=True,
    )

    # UCL member only
    person = models.ForeignKey(
        'base.Person',
        verbose_name=_("Person"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    # External member only
    institute = models.CharField(
        verbose_name=pgettext_lazy('jury', 'Institute'),
        max_length=255,
        default='',
        blank=True,
    )
    country = models.ForeignKey(
        'reference.Country',
        verbose_name=_("Country"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    last_name = models.CharField(
        verbose_name=_('Surname'),
        max_length=255,
        default='',
        blank=True,
    )
    first_name = models.CharField(
        verbose_name=_('First name'),
        max_length=255,
        default='',
        blank=True,
    )
    title = models.CharField(
        verbose_name=pgettext_lazy('admission', 'Title'),
        choices=TitreMembre.choices(),
        max_length=50,
        default='',
        blank=True,
    )
    non_doctor_reason = models.TextField(
        verbose_name=_('Non doctor reason'),
        max_length=255,
        default='',
        blank=True,
    )
    gender = models.CharField(
        verbose_name=_('Gender'),
        choices=GenreMembre.choices(),
        max_length=50,
        default='',
        blank=True,
    )
    email = models.EmailField(
        verbose_name=pgettext_lazy('admission', 'Email'),
        max_length=255,
        default='',
        blank=True,
    )

    class Meta:
        constraints = [
            CheckConstraint(
                check=(
                    Q(promoter__isnull=False)
                    & Q(person__isnull=True)
                    & Q(institute='')
                    & Q(other_institute='')
                    & Q(country__isnull=True)
                    & Q(last_name='')
                    & Q(first_name='')
                    & Q(title='')
                    & Q(gender='')
                    & Q(email='')
                )
                | (
                    Q(promoter__isnull=True)
                    & Q(person__isnull=False)
                    & Q(institute='')
                    & Q(country__isnull=True)
                    & Q(last_name='')
                    & Q(first_name='')
                    & Q(title='')
                    & Q(gender='')
                    & Q(email='')
                )
                | (
                    Q(promoter__isnull=True)
                    & Q(person__isnull=True)
                    & ~Q(institute='')
                    & Q(country__isnull=False)
                    & ~Q(last_name='')
                    & ~Q(first_name='')
                    & ~Q(title='')
                    & ~Q(gender='')
                    & ~Q(email='')
                ),
                name='admission_jurymember_constraint',
            ),
        ]

    @property
    def complete_name(self):
        if self.promoter_id:
            return f"{self.promoter.last_name}, {self.promoter.first_name}"

        if self.person_id:
            return f"{self.person.last_name}, {self.person.first_name}"

        return f"{self.last_name}, {self.first_name}"
