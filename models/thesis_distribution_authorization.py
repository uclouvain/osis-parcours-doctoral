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
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from osis_signature.contrib.fields import SignatureProcessField
from osis_signature.models import Actor

from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.enums import (
    ChoixStatutAutorisationDiffusionThese,
    RoleActeur,
    TypeModalitesDiffusionThese,
)

__all__ = [
    'ThesisDistributionAuthorization',
    'ThesisDistributionAuthorizationActor',
]


class ThesisDistributionAuthorization(models.Model):
    parcours_doctoral = models.OneToOneField(
        verbose_name=_('Doctorate'),
        to='parcours_doctoral.ParcoursDoctoral',
        on_delete=models.CASCADE,
        related_name='thesis_distribution_authorization',
    )

    status = models.CharField(
        verbose_name=_('Status'),
        choices=ChoixStatutAutorisationDiffusionThese.choices(),
        default=ChoixStatutAutorisationDiffusionThese.DIFFUSION_NON_SOUMISE.name,
        max_length=30,
    )

    funding_sources = models.CharField(
        verbose_name=_('Sources of funding throughout PhD'),
        default='',
        blank=True,
        max_length=100,
    )

    thesis_summary_in_english = models.CharField(
        verbose_name=_('Summary in English'),
        default='',
        blank=True,
        max_length=100,
    )

    thesis_summary_in_other_language = models.CharField(
        verbose_name=_('Summary in other language'),
        default='',
        blank=True,
        max_length=100,
    )

    thesis_keywords = ArrayField(
        base_field=models.CharField(
            max_length=50,
        ),
        blank=True,
        default=list,
    )

    conditions = models.CharField(
        verbose_name=_('Conditions'),
        choices=TypeModalitesDiffusionThese.choices(),
        blank=True,
        default='',
        max_length=30,
    )

    embargo_date = models.DateField(
        verbose_name=_('Embargo date'),
        null=True,
        blank=True,
    )

    additional_limitation_for_specific_chapters = models.TextField(
        verbose_name=_('Additional limitation for certain specific chapters'),
        default='',
        blank=True,
    )

    accepted_on = models.DateField(
        verbose_name=_('Acceptation date'),
        blank=True,
        null=True,
    )

    acceptation_content = models.TextField(
        verbose_name=_('Acceptation content'),
        default='',
        blank=True,
    )

    signature_group = SignatureProcessField()


class ThesisDistributionAuthorizationActor(Actor):
    """This model extends Actor from OSIS-Signature"""

    role = models.CharField(
        verbose_name=_('Role'),
        choices=RoleActeur.choices(),
        max_length=50,
    )
    internal_comment = models.TextField(
        default='',
        verbose_name=_('Internal comment'),
        blank=True,
    )
    rejection_reason = models.CharField(
        default='',
        max_length=50,
        blank=True,
        verbose_name=_('Grounds for denied'),
    )
