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

from base.models.enums.organization_type import MAIN
from django.conf import settings
from django.db import models
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from parcours_doctoral.ddd.formation.domain.model.enums import CategorieActivite
from parcours_doctoral.forms.translation_field import (
    TextareaArrayField,
    TranslatedTextareasWidget,
    TranslatedValueField,
)

__all__ = [
    'CddConfiguration',
]


def default_category_labels():
    choices = dict(CategorieActivite.choices()).values()
    ret = {}
    for lang in [settings.LANGUAGE_CODE_EN, settings.LANGUAGE_CODE_FR]:
        with translation.override(lang):
            ret[lang] = [str(choice) for choice in choices]
    return ret


def default_service_types():
    return {
        settings.LANGUAGE_CODE_EN: [
            "Didactic supervision",
            "Teaching activities",
            "Popularisation of science",
            "Writing a research project",
            "Organisation of scientific events",
            "Scientific expertise report (refering)",
            "Supervision of dissertations",
            "International cooperation",
        ],
        settings.LANGUAGE_CODE_FR: [
            "Encadrement didactique",
            "Activités d'enseignement",
            "Vulgarisation scientifique",
            "Rédaction d'un projet de recherche",
            "Organisation de manifestation scientifique",
            "Rapport d’expertise scientifique (refering)",
            "Supervision de mémoire",
            "Coopération internationale",
        ],
    }


def default_seminar_types():
    return {
        settings.LANGUAGE_CODE_EN: [
            "Research seminar",
            "PhD students' day",
        ],
        settings.LANGUAGE_CODE_FR: [
            "Séminaire de recherche",
            "Journée des doctorantes et des doctorants",
        ],
    }


def default_conference_types():
    return {
        settings.LANGUAGE_CODE_EN: [
            "National conference",
            "International conference",
        ],
        settings.LANGUAGE_CODE_FR: [
            "Conférence nationale",
            "Conférence internationale",
        ],
    }


def default_conference_publication_types():
    return {
        settings.LANGUAGE_CODE_EN: [
            "Article published in a peer-reviewed journal",
            "Article published in a non-refereed journal",
            "Book chapter",
            "Monograph",
            "Edition or co-publication",
            "Working paper",
            "Extended abstract",
        ],
        settings.LANGUAGE_CODE_FR: [
            "Article publié dans une revue à comité de lecture",
            "Article publié dans une revue sans comité de lecture",
            "Chapitre de livre",
            "Monographie",
            "Édition ou coédition",
            "Rapport de recherche",
            "Extended abstract",
        ],
    }


def default_communication_types():
    return {
        settings.LANGUAGE_CODE_EN: [
            "Research seminar",
            "PhD students' day",
        ],
        settings.LANGUAGE_CODE_FR: [
            "Séminaire de recherche",
            "Journée des doctorantes et des doctorants",
        ],
    }


def default_publication_types():
    return {
        settings.LANGUAGE_CODE_EN: [
            "Article for a peer-reviewed journal",
            "Article for a non-refereed journal",
            "Publication in an international scientific journal with peer review",
            "Book chapter",
            "Monograph",
            "Publishing or co-publishing",
            "Patent",
            "Review of a scientific work",
            "Working paper",
        ],
        settings.LANGUAGE_CODE_FR: [
            "Article à destination d'une revue à comité de lecture",
            "Article à destination d'une revue sans comité de lecture",
            "Publication dans une revue scientifique internationale avec peer review",
            "Chapitre de livre",
            "Monographie",
            "Édition ou coédition",
            "Brevet",
            "Compte - rendu d'un ouvrage scientifique",
            "Rapport de recherche",
        ],
    }


def default_residency_types():
    return {
        settings.LANGUAGE_CODE_EN: [
            "Research residency (excluding cotutelle)",
            "Documentary research residency",
        ],
        settings.LANGUAGE_CODE_FR: [
            "Séjour de recherche (hors cotutelle)",
            "Séjour de recherche documentaire",
        ],
    }


def default_course_types():
    return {
        settings.LANGUAGE_CODE_EN: [
            "Graduate course",
            "Doctoral school (with/without assessment)",
            "Continuing education",
            "Transversal training",
            "Summer school",
            "Winter school",
            "Language courses",
            "Moocs (online / offline)",
        ],
        settings.LANGUAGE_CODE_FR: [
            "Cours de 2e cycle",
            "Ecole doctorale (avec/sans évaluation)",
            "Formation continuée",
            "Formation transversale",
            "Summer school",
            "Winter school",
            "Cours de langue",
            "Moocs (en ligne / pas en ligne)",
        ],
    }


def default_complementary_course_types():
    return {
        settings.LANGUAGE_CODE_EN: [
            "Graduate course",
            "Doctoral school (with/without assessment)",
            "Continuing education",
            "Transversal training",
            "Language courses",
            "Moocs (online / offline)",
        ],
        settings.LANGUAGE_CODE_FR: [
            "Cours de 2e cycle",
            "Ecole doctorale (avec/sans évaluation)",
            "Formation continuée",
            "Formation transversale",
            "Cours de langue",
            "Moocs (en ligne / pas en ligne)",
        ],
    }


class TranslatedMultilineField(models.JSONField):
    def formfield(self, form_class=None, choices_form_class=None, **kwargs):
        kwargs.setdefault('form_class', TranslatedValueField)
        kwargs.setdefault('help_text', _('One choice per line, leave the "Other" value out'))
        kwargs.setdefault('base_field', TextareaArrayField)
        kwargs.setdefault('widget', TranslatedTextareasWidget())
        return super().formfield(**kwargs)


class CddConfiguration(models.Model):
    cdd = models.OneToOneField(
        'base.Entity',
        on_delete=models.CASCADE,
        limit_choices_to={'organization__type': MAIN},
        related_name='doctorate_config',
    )
    is_complementary_training_enabled = models.BooleanField(
        verbose_name=_("Enable complementary training tab"),
        default=False,
        help_text=_('This adds a "Complementary training" tab on admissions concerning this CDD.'),
    )
    category_labels = TranslatedMultilineField(
        verbose_name=_("Category labels"),
        default=default_category_labels,
    )
    conference_types = TranslatedMultilineField(
        verbose_name=_("CONFERENCE types"),
        default=default_conference_types,
    )
    conference_publication_types = TranslatedMultilineField(
        verbose_name=_("CONFERENCE PUBLICATION types"),
        default=default_conference_publication_types,
    )
    communication_types = TranslatedMultilineField(
        verbose_name=_("COMMUNICATION types"),
        default=default_communication_types,
    )
    seminar_types = TranslatedMultilineField(
        verbose_name=_("SEMINAR types"),
        default=default_seminar_types,
    )
    publication_types = TranslatedMultilineField(
        verbose_name=_("PUBLICATION types"),
        default=default_publication_types,
    )
    service_types = TranslatedMultilineField(
        verbose_name=_("SERVICE types"),
        default=default_service_types,
    )
    residency_types = TranslatedMultilineField(
        verbose_name=_("RESIDENCY types"),
        default=default_residency_types,
    )
    course_types = TranslatedMultilineField(
        verbose_name=_("COURSE types"),
        default=default_course_types,
    )
    complementary_course_types = TranslatedMultilineField(
        verbose_name=_("COURSE types for complementary training"),
        default=default_complementary_course_types,
    )

    def __str__(self):  # pragma: no cover
        return f"Configuration for {self.cdd}"
