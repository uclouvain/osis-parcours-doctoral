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
from typing import List

from django.conf import settings
from django.db.models import QuerySet
from django.utils import translation
from django.utils.functional import Promise, lazy
from django.utils.translation import get_language, override
from django.utils.translation import gettext_lazy as _
from osis_mail_template import generate_email
from osis_notification.contrib.handlers import (
    EmailNotificationHandler,
    WebNotificationHandler,
)
from osis_notification.contrib.notification import WebNotification
from osis_notification.models.enums import NotificationTypes
from osis_notification.models.web_notification import WebNotification as WebNotificationDBModel
from osis_signature.models import Actor

from base.auth.roles.program_manager import ProgramManager
from parcours_doctoral.ddd.domain.model._promoteur import PromoteurIdentity
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoral
from parcours_doctoral.ddd.formation.domain.model.activite import Activite
from parcours_doctoral.ddd.formation.domain.model.enums import (
    CategorieActivite,
    ContexteFormation,
    StatutActivite,
)
from parcours_doctoral.ddd.formation.domain.model.evaluation import Evaluation
from parcours_doctoral.ddd.formation.domain.service.i_notification import INotification
from parcours_doctoral.mail_templates import (
    PARCOURS_DOCTORAL_EMAIL_REFERENCE_PROMOTER_COMPLEMENTARY_TRAININGS_SUBMITTED,
    PARCOURS_DOCTORAL_EMAIL_REFERENCE_PROMOTER_COURSE_ENROLLMENTS_SUBMITTED,
    PARCOURS_DOCTORAL_EMAIL_REFERENCE_PROMOTER_DOCTORAL_TRAININGS_SUBMITTED,
    PARCOURS_DOCTORAL_EMAIL_STUDENT_COMPLEMENTARY_TRAINING_NEEDS_UPDATE,
    PARCOURS_DOCTORAL_EMAIL_STUDENT_COMPLEMENTARY_TRAINING_REFUSED,
    PARCOURS_DOCTORAL_EMAIL_STUDENT_COURSE_ENROLLMENT_NEEDS_UPDATE,
    PARCOURS_DOCTORAL_EMAIL_STUDENT_COURSE_ENROLLMENT_REFUSED,
    PARCOURS_DOCTORAL_EMAIL_STUDENT_DOCTORAL_TRAINING_NEEDS_UPDATE,
    PARCOURS_DOCTORAL_EMAIL_STUDENT_DOCTORAL_TRAINING_REFUSED,
)
from parcours_doctoral.models.activity import Activity
from parcours_doctoral.models.parcours_doctoral import (
    ParcoursDoctoral as ParcoursDoctoralModel,
)
from parcours_doctoral.utils.url import (
    get_parcours_doctoral_link_back,
    get_parcours_doctoral_link_front,
)


class Notification(INotification):
    @classmethod
    def _get_doctorate(cls, doctorate_uuid):
        return ParcoursDoctoralModel.objects.select_related(
            'student',
            'training',
        ).get(uuid=doctorate_uuid)

    @classmethod
    def _get_parcours_doctoral_title_translation(cls, parcours_doctoral: ParcoursDoctoral) -> Promise:
        """Populate the translations of the doctorate title and lazy return them"""
        # Create a dict to cache the translations of the doctorate title
        parcours_doctoral_title = {
            settings.LANGUAGE_CODE_EN: parcours_doctoral.training.title_english,
            settings.LANGUAGE_CODE_FR: parcours_doctoral.training.title,
        }

        # Return a lazy proxy which, when evaluated to string, return the correct translation given the current language
        return lazy(lambda: parcours_doctoral_title[get_language()], str)()

    @classmethod
    def get_common_tokens(
        cls,
        parcours_doctoral: ParcoursDoctoralModel,
    ) -> dict:
        """Return common tokens about a doctorate"""
        return {
            "student_first_name": parcours_doctoral.student.first_name,
            "student_last_name": parcours_doctoral.student.last_name,
            "training_title": cls._get_parcours_doctoral_title_translation(parcours_doctoral),
            "parcours_doctoral_link_front": get_parcours_doctoral_link_front(parcours_doctoral.uuid),
            "parcours_doctoral_link_front_doctoral_training": get_parcours_doctoral_link_front(
                parcours_doctoral.uuid,
                'doctoral-training',
            ),
            "parcours_doctoral_link_front_complementary_training": get_parcours_doctoral_link_front(
                parcours_doctoral.uuid,
                'complementary-training',
            ),
            "parcours_doctoral_link_front_course_enrollment": get_parcours_doctoral_link_front(
                parcours_doctoral.uuid,
                'course-enrollment',
            ),
            "parcours_doctoral_link_back": get_parcours_doctoral_link_back(parcours_doctoral.uuid),
            "parcours_doctoral_link_back_doctoral_training": get_parcours_doctoral_link_back(
                parcours_doctoral.uuid,
                'doctoral-training',
            ),
            "parcours_doctoral_link_back_complementary_training": get_parcours_doctoral_link_back(
                parcours_doctoral.uuid,
                'complementary-training',
            ),
            "parcours_doctoral_link_back_course_enrollment": get_parcours_doctoral_link_back(
                parcours_doctoral.uuid,
                'course-enrollment',
            ),
        }

    @classmethod
    def _get_mail_template_ids(cls, activite: Activite):
        if activite.categorie == CategorieActivite.UCL_COURSE:
            return {
                'submitted': PARCOURS_DOCTORAL_EMAIL_REFERENCE_PROMOTER_COURSE_ENROLLMENTS_SUBMITTED,
                'refusal': PARCOURS_DOCTORAL_EMAIL_STUDENT_COURSE_ENROLLMENT_REFUSED,
                'needs-update': PARCOURS_DOCTORAL_EMAIL_STUDENT_COURSE_ENROLLMENT_NEEDS_UPDATE,
            }
        elif activite.contexte == ContexteFormation.COMPLEMENTARY_TRAINING:
            return {
                'submitted': PARCOURS_DOCTORAL_EMAIL_REFERENCE_PROMOTER_COMPLEMENTARY_TRAININGS_SUBMITTED,
                'refusal': PARCOURS_DOCTORAL_EMAIL_STUDENT_COMPLEMENTARY_TRAINING_REFUSED,
                'needs-update': PARCOURS_DOCTORAL_EMAIL_STUDENT_COMPLEMENTARY_TRAINING_NEEDS_UPDATE,
            }
        return {
            'submitted': PARCOURS_DOCTORAL_EMAIL_REFERENCE_PROMOTER_DOCTORAL_TRAININGS_SUBMITTED,
            'refusal': PARCOURS_DOCTORAL_EMAIL_STUDENT_DOCTORAL_TRAINING_REFUSED,
            'needs-update': PARCOURS_DOCTORAL_EMAIL_STUDENT_DOCTORAL_TRAINING_NEEDS_UPDATE,
        }

    @classmethod
    def notifier_soumission_au_promoteur_de_reference(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        activites: List[Activite],
        promoteur_de_reference_id: PromoteurIdentity,
    ) -> None:
        parcours_doctoral_instance = cls._get_doctorate(doctorate_uuid=parcours_doctoral.entity_id.uuid)
        common_tokens = cls.get_common_tokens(parcours_doctoral_instance)
        promoteur = Actor.objects.get(uuid=promoteur_de_reference_id.uuid)

        email_message = generate_email(
            cls._get_mail_template_ids(activites[0])['submitted'],
            promoteur.language,
            common_tokens,
            recipients=[promoteur.email],
        )
        EmailNotificationHandler.create(email_message, person=promoteur.person_id and promoteur.person)

    @classmethod
    def notifier_validation_au_doctorant(cls, parcours_doctoral: ParcoursDoctoral, activites: List[Activite]) -> None:
        parcours_doctoral_instance = cls._get_doctorate(doctorate_uuid=parcours_doctoral.entity_id.uuid)
        common_tokens = cls.get_common_tokens(parcours_doctoral_instance)
        if activites[0].categorie == CategorieActivite.UCL_COURSE:
            msg = _(
                '<a href="%(parcours_doctoral_link_front_course_enrollment)s">PhD</a> - '
                'Some course enrollment have been approved.'
            )
        elif activites[0].contexte == ContexteFormation.COMPLEMENTARY_TRAINING:
            msg = _(
                '<a href="%(parcours_doctoral_link_front_complementary_training)s">PhD</a> - '
                'Some complementary training activities have been approved.'
            )
        else:
            msg = _(
                '<a href="%(parcours_doctoral_link_front_doctoral_training)s">PhD</a> - '
                'Some doctoral training activities have been approved.'
            )
        with translation.override(parcours_doctoral_instance.student.language):
            content = msg % common_tokens
        web_notification = WebNotification(recipient=parcours_doctoral_instance.student, content=content)
        WebNotificationHandler.create(web_notification)

    @classmethod
    def notifier_refus_au_candidat(cls, parcours_doctoral, activite):
        parcours_doctoral_instance = cls._get_doctorate(doctorate_uuid=parcours_doctoral.entity_id.uuid)
        common_tokens = cls.get_common_tokens(parcours_doctoral_instance)

        mail_template_id = cls._get_mail_template_ids(activite).get(
            'refusal' if activite.statut == StatutActivite.REFUSEE else 'needs-update'
        )
        email_message = generate_email(
            mail_template_id,
            parcours_doctoral_instance.student.language,
            {
                **common_tokens,
                'reason': activite.commentaire_gestionnaire,
                'activity_title': str(Activity.objects.get(uuid=activite.entity_id.uuid)),
            },
            recipients=[parcours_doctoral_instance.student.email],
        )
        EmailNotificationHandler.create(email_message, person=parcours_doctoral_instance.student)

    @classmethod
    def notifier_encodage_note_aux_gestionnaires(cls, evaluation: Evaluation, cours: Activite) -> None:
        doctorate = (
            ParcoursDoctoralModel.objects.filter(uuid=cours.parcours_doctoral_id.uuid)
            .values('uuid', 'training__education_group_id')
            .first()
        )

        if not doctorate:
            return

        program_managers: QuerySet[ProgramManager] = ProgramManager.objects.filter(
            education_group_id=doctorate['training__education_group_id']
        ).select_related('person')

        assessment_enrolment_list_url = get_parcours_doctoral_link_back(doctorate['uuid'], 'assessment-enrollment')

        content = _(
            '<a href="%(assessment_enrolment_list_url)s">PhD</a> - '
            'A mark has been specified for an assessment '
            '(%(course_acronym)s - session numero %(session)s - %(course_year)s-%(course_year_1)s).'
        )
        tokens = {
            'assessment_enrolment_list_url': assessment_enrolment_list_url,
            'course_acronym': evaluation.entity_id.code_unite_enseignement,
            'session': evaluation.entity_id.session,
            'course_year': evaluation.entity_id.annee,
            'course_year_1': evaluation.entity_id.annee + 1,
        }

        web_notifications: list[WebNotificationDBModel] = []
        for manager in program_managers:
            with override(manager.person.language):
                web_notifications.append(
                    WebNotificationDBModel(
                        person=manager.person,
                        payload=str(content % tokens),
                        type=NotificationTypes.WEB_TYPE.name,
                    )
                )
        WebNotificationDBModel.objects.bulk_create(objs=web_notifications)
