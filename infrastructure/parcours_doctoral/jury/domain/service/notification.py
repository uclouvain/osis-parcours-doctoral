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

from email.message import EmailMessage

from django.conf import settings
from django.utils import translation
from django.utils.functional import lazy
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from osis_async.models import AsyncTask
from osis_mail_template.utils import generate_email, transform_html_to_text
from osis_notification.contrib.handlers import (
    EmailNotificationHandler,
    WebNotificationHandler,
)
from osis_notification.contrib.notification import EmailNotification
from osis_notification.models import WebNotification
from osis_signature.enums import SignatureState
from osis_signature.utils import get_signing_token

from base.models.person import Person
from parcours_doctoral.ddd.domain.model.groupe_de_supervision import (
    GroupeDeSupervision,
    SignataireIdentity,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoral
from parcours_doctoral.ddd.domain.validator.exceptions import (
    SignataireNonTrouveException,
)
from parcours_doctoral.ddd.jury.domain.model.jury import Jury
from parcours_doctoral.ddd.jury.domain.service.i_notification import INotification
from parcours_doctoral.mail_templates.signatures import (
    PARCOURS_DOCTORAL_EMAIL_MEMBER_REMOVED,
    PARCOURS_DOCTORAL_EMAIL_SIGNATURE_REQUESTS_ACTOR,
    PARCOURS_DOCTORAL_EMAIL_SIGNATURE_REQUESTS_STUDENT,
)
from parcours_doctoral.models import ActorType, ParcoursDoctoralSupervisionActor
from parcours_doctoral.models.parcours_doctoral import (
    ParcoursDoctoral as ParcoursDoctoralModel,
)
from parcours_doctoral.models.task import ParcoursDoctoralTask
from parcours_doctoral.utils.persons import get_parcours_doctoral_cdd_managers
from parcours_doctoral.utils.url import (
    get_parcours_doctoral_link_back,
    get_parcours_doctoral_link_front,
)


class Notification(INotification):

    @classmethod
    def envoyer_signatures(
            cls, parcours_doctoral: ParcoursDoctoral, jury: Jury
    ) -> None:
        parcours_doctoral_instance = ParcoursDoctoralModel.objects.get(uuid=parcours_doctoral.entity_id.uuid)

        # Création de la tâche de génération du document
        task = AsyncTask.objects.create(
            name=_("Exporting %(reference)s to PDF") % {'reference': parcours_doctoral.reference},
            description=_("Exporting the admission information to PDF"),
            person=parcours_doctoral_instance.student,
            time_to_live=5,
        )
        ParcoursDoctoralTask.objects.create(
            task=task,
            parcours_doctoral=parcours_doctoral_instance,
            type=ParcoursDoctoralTask.TaskType.ARCHIVE.name,
        )

        # Tokens communs
        doctorant = Person.objects.get(global_id=parcours_doctoral.matricule_doctorant)
        common_tokens = cls.get_common_tokens(parcours_doctoral_instance)
        common_tokens["parcours_doctoral_link_back"] = get_parcours_doctoral_link_back(
            uuid=parcours_doctoral_instance.entity_id.uuid,
            tab='supervision',
        )
        common_tokens["parcours_doctoral_link_front"] = get_parcours_doctoral_link_front(
            uuid=parcours_doctoral_instance.entity_id.uuid,
            tab='supervision',
        )
        actor_list = ParcoursDoctoralSupervisionActor.objects.filter(
            process=parcours_doctoral_instance.supervision_group
        ).select_related('person')

        # Envoyer aux gestionnaires CDD
        for manager in get_parcours_doctoral_cdd_managers(parcours_doctoral_instance.training.education_group_id):
            with translation.override(manager.language):
                content = (
                    _(
                        '<a href="%(parcours_doctoral_link_back)s">%(reference)s</a> - '
                        '%(student_first_name)s %(student_last_name)s requested '
                        'signatures for %(training_title)s'
                    )
                    % common_tokens
                )
                web_notification = WebNotification(recipient=manager, content=str(content))
            WebNotificationHandler.create(web_notification)

        # Envoyer au doctorant
        with translation.override(doctorant.language):
            actor_list_str = [
                f"{actor.first_name} {actor.last_name} ({actor.get_type_display()})" for actor in actor_list
            ]
        email_message = generate_email(
            PARCOURS_DOCTORAL_EMAIL_SIGNATURE_REQUESTS_STUDENT,
            doctorant.language,
            {
                **common_tokens,
                "actors_as_list_items": '<li></li>'.join(actor_list_str),
                "actors_comma_separated": ', '.join(actor_list_str),
            },
            recipients=[doctorant.email],
        )
        EmailNotificationHandler.create(email_message, person=doctorant)

        # Envoyer aux acteurs n'ayant pas répondu
        actors_invited = [actor for actor in actor_list if actor.last_state == SignatureState.INVITED.name]
        for actor in actors_invited:
            tokens = {
                **common_tokens,
                "signataire_first_name": actor.first_name,
                "signataire_last_name": actor.last_name,
                "signataire_role": actor.get_type_display(),
            }
            if actor.is_external:
                tokens["parcours_doctoral_link_front"] = cls._lien_invitation_externe(parcours_doctoral, actor)
            email_message = generate_email(
                PARCOURS_DOCTORAL_EMAIL_SIGNATURE_REQUESTS_ACTOR,
                actor.language,
                tokens,
                recipients=[actor.email],
            )
            EmailNotificationHandler.create(email_message, person=actor.person_id and actor.person)
