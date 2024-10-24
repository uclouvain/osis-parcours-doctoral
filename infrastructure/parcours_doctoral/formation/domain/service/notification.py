# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List, Union

from django.conf import settings
from django.shortcuts import resolve_url
from django.utils import translation
from django.utils.functional import Promise, lazy
from django.utils.translation import get_language, gettext_lazy as _

from admission.contrib.models import DoctorateAdmission
from parcours_doctoral.models.doctoral_training import Activity
from admission.contrib.models.doctorate import ParcoursDoctoral
from admission.ddd.admission.doctorat.preparation.commands import UUID
from admission.ddd.admission.doctorat.preparation.domain.model._promoteur import PromoteurIdentity
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoral
from parcours_doctoral.ddd.formation.domain.model.activite import Activite
from parcours_doctoral.ddd.formation.domain.model.enums import (
    CategorieActivite,
    ContexteFormation,
    StatutActivite,
)
from parcours_doctoral.ddd.formation.domain.service.i_notification import INotification
from parcours_doctoral.mail_templates import (
    ADMISSION_EMAIL_CANDIDATE_COMPLEMENTARY_TRAINING_NEEDS_UPDATE,
    ADMISSION_EMAIL_CANDIDATE_COMPLEMENTARY_TRAINING_REFUSED,
    ADMISSION_EMAIL_CANDIDATE_COURSE_ENROLLMENT_NEEDS_UPDATE,
    ADMISSION_EMAIL_CANDIDATE_COURSE_ENROLLMENT_REFUSED,
    ADMISSION_EMAIL_CANDIDATE_DOCTORAL_TRAINING_NEEDS_UPDATE,
    ADMISSION_EMAIL_CANDIDATE_DOCTORAL_TRAINING_REFUSED,
    ADMISSION_EMAIL_REFERENCE_PROMOTER_COMPLEMENTARY_TRAININGS_SUBMITTED,
    ADMISSION_EMAIL_REFERENCE_PROMOTER_COURSE_ENROLLMENTS_SUBMITTED,
    ADMISSION_EMAIL_REFERENCE_PROMOTER_DOCTORAL_TRAININGS_SUBMITTED,
)
from base.models.person import Person
from osis_mail_template import generate_email
from osis_notification.contrib.handlers import EmailNotificationHandler, WebNotificationHandler
from osis_notification.contrib.notification import WebNotification
from osis_signature.models import Actor


class Notification(INotification):
    @classmethod
    def get_admission_link_front(cls, uuid: UUID, tab='') -> str:
        return settings.ADMISSION_FRONTEND_LINK.format(context='doctorate', uuid=uuid) + tab

    @classmethod
    def _get_doctorate_title_translation(cls, doctorate: Union[ParcoursDoctoral, DoctorateAdmission]) -> Promise:
        """Populate the translations of the doctorate title and lazy return them"""
        # Create a dict to cache the translations of the doctorate title
        doctorate_title = {
            settings.LANGUAGE_CODE_EN: doctorate.doctorate.title_english,
            settings.LANGUAGE_CODE_FR: doctorate.doctorate.title,
        }

        # Return a lazy proxy which, when evaluated to string, return the correct translation given the current language
        return lazy(lambda: doctorate_title[get_language()], str)()

    @classmethod
    def get_common_tokens(
        cls,
        doctorate: Union[ParcoursDoctoral, DoctorateAdmission],
    ) -> dict:
        """Return common tokens about a doctorate"""
        return {
            "student_first_name": doctorate.candidate.first_name,
            "student_last_name": doctorate.candidate.last_name,
            "training_title": cls._get_doctorate_title_translation(doctorate),
            "admission_link_front": cls.get_admission_link_front(doctorate.uuid),
            "admission_link_front_doctoral_training": cls.get_admission_link_front(doctorate.uuid, 'doctoral-training'),
            "admission_link_front_complementary_training": cls.get_admission_link_front(
                doctorate.uuid, 'complementary-training'
            ),
            "admission_link_front_course_enrollment": cls.get_admission_link_front(doctorate.uuid, 'course-enrollment'),
            "admission_link_back": "{}{}".format(
                settings.ADMISSION_BACKEND_LINK_PREFIX,
                resolve_url('admission:doctorate:project', uuid=doctorate.uuid),
            ),
            "admission_link_back_doctoral_training": "{}{}".format(
                settings.ADMISSION_BACKEND_LINK_PREFIX,
                resolve_url('admission:doctorate:doctoral-training', uuid=doctorate.uuid),
            ),
            "admission_link_back_complementary_training": "{}{}".format(
                settings.ADMISSION_BACKEND_LINK_PREFIX,
                resolve_url('admission:doctorate:complementary-training', uuid=doctorate.uuid),
            ),
            "admission_link_back_course_enrollment": "{}{}".format(
                settings.ADMISSION_BACKEND_LINK_PREFIX,
                resolve_url('admission:doctorate:course-enrollment', uuid=doctorate.uuid),
            ),
            "reference": doctorate.reference,
        }

    @classmethod
    def _get_mail_template_ids(cls, activite: Activite):
        if activite.categorie == CategorieActivite.UCL_COURSE:
            return {
                'submitted': ADMISSION_EMAIL_REFERENCE_PROMOTER_COURSE_ENROLLMENTS_SUBMITTED,
                'refusal': ADMISSION_EMAIL_CANDIDATE_COURSE_ENROLLMENT_REFUSED,
                'needs-update': ADMISSION_EMAIL_CANDIDATE_COURSE_ENROLLMENT_NEEDS_UPDATE,
            }
        elif activite.contexte == ContexteFormation.COMPLEMENTARY_TRAINING:
            return {
                'submitted': ADMISSION_EMAIL_REFERENCE_PROMOTER_COMPLEMENTARY_TRAININGS_SUBMITTED,
                'refusal': ADMISSION_EMAIL_CANDIDATE_COMPLEMENTARY_TRAINING_REFUSED,
                'needs-update': ADMISSION_EMAIL_CANDIDATE_COMPLEMENTARY_TRAINING_NEEDS_UPDATE,
            }
        return {
            'submitted': ADMISSION_EMAIL_REFERENCE_PROMOTER_DOCTORAL_TRAININGS_SUBMITTED,
            'refusal': ADMISSION_EMAIL_CANDIDATE_DOCTORAL_TRAINING_REFUSED,
            'needs-update': ADMISSION_EMAIL_CANDIDATE_DOCTORAL_TRAINING_NEEDS_UPDATE,
        }

    @classmethod
    def notifier_soumission_au_promoteur_de_reference(
        cls,
        doctorat: ParcoursDoctoral,
        activites: List[Activite],
        promoteur_de_reference_id: PromoteurIdentity,
    ) -> None:
        doctorate: ParcoursDoctoral = ParcoursDoctoral.objects.get(uuid=doctorat.entity_id.uuid)
        common_tokens = cls.get_common_tokens(doctorate)
        promoteur = Actor.objects.get(uuid=promoteur_de_reference_id.uuid)

        email_message = generate_email(
            cls._get_mail_template_ids(activites[0])['submitted'],
            promoteur.language,
            common_tokens,
            recipients=[promoteur.email],
        )
        EmailNotificationHandler.create(email_message, person=promoteur.person_id and promoteur.person)

    @classmethod
    def notifier_validation_au_candidat(cls, doctorat: ParcoursDoctoral, activites: List[Activite]) -> None:
        doctorate: ParcoursDoctoral = ParcoursDoctoral.objects.get(uuid=doctorat.entity_id.uuid)
        candidat = Person.objects.get(global_id=doctorat.matricule_doctorant)
        common_tokens = cls.get_common_tokens(doctorate)
        if activites[0].categorie == CategorieActivite.UCL_COURSE:
            msg = _(
                '<a href="%(admission_link_front_course_enrollment)s">%(reference)s</a> - '
                'Some course enrollment have been approved.'
            )
        elif activites[0].contexte == ContexteFormation.COMPLEMENTARY_TRAINING:
            msg = _(
                '<a href="%(admission_link_front_complementary_training)s">%(reference)s</a> - '
                'Some complementary training activities have been approved.'
            )
        else:
            msg = _(
                '<a href="%(admission_link_front_doctoral_training)s">%(reference)s</a> - '
                'Some doctoral training activities have been approved.'
            )
        with translation.override(candidat.language):
            content = msg % common_tokens
        web_notification = WebNotification(recipient=candidat, content=content)
        WebNotificationHandler.create(web_notification)

    @classmethod
    def notifier_refus_au_candidat(cls, doctorat, activite):
        doctorate: ParcoursDoctoral = ParcoursDoctoral.objects.get(uuid=doctorat.entity_id.uuid)
        common_tokens = cls.get_common_tokens(doctorate)

        mail_template_id = cls._get_mail_template_ids(activite).get(
            'refusal' if activite.statut == StatutActivite.REFUSEE else 'needs-update'
        )
        email_message = generate_email(
            mail_template_id,
            doctorate.candidate.language,
            {
                **common_tokens,
                'reason': activite.commentaire_gestionnaire,
                'activity_title': str(Activity.objects.get(uuid=activite.entity_id.uuid)),
            },
            recipients=[doctorate.candidate.email],
        )
        EmailNotificationHandler.create(email_message, person=doctorate.candidate)
