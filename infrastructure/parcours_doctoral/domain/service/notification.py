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
from parcours_doctoral.ddd.domain.service.i_notification import INotification
from parcours_doctoral.ddd.domain.validator.exceptions import (
    SignataireNonTrouveException,
)
from parcours_doctoral.infrastructure.mixins.notification import NotificationMixin
from parcours_doctoral.mail_templates.signatures import (
    PARCOURS_DOCTORAL_EMAIL_MEMBER_REMOVED,
    PARCOURS_DOCTORAL_EMAIL_SIGNATURE_REQUESTS_ACTOR,
    PARCOURS_DOCTORAL_EMAIL_SIGNATURE_REQUESTS_STUDENT,
)
from parcours_doctoral.models import (
    ActorType,
    JuryMember,
    ParcoursDoctoralSupervisionActor,
)
from parcours_doctoral.models.parcours_doctoral import (
    ParcoursDoctoral as ParcoursDoctoralModel,
)
from parcours_doctoral.models.task import ParcoursDoctoralTask
from parcours_doctoral.utils.persons import get_parcours_doctoral_cdd_managers
from parcours_doctoral.utils.url import (
    get_parcours_doctoral_link_back,
    get_parcours_doctoral_link_front,
)


class Notification(NotificationMixin, INotification):
    @classmethod
    def envoyer_message(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        matricule_emetteur: str,
        matricule_doctorant: str,
        sujet: str,
        message: str,
        cc_promoteurs: bool,
        cc_membres_ca: bool,
        cc_jury: bool = False,
    ) -> EmailMessage:
        parcours_doctoral_instance = ParcoursDoctoralModel.objects.get(uuid=parcours_doctoral.entity_id.uuid)

        # Notifier le doctorant via mail
        email_message = EmailNotificationHandler.build(
            EmailNotification(
                parcours_doctoral_instance.student,
                sujet,
                transform_html_to_text(message),
                message,
            )
        )

        cc_list = set()

        if cc_promoteurs or cc_membres_ca:
            actors = ParcoursDoctoralSupervisionActor.objects.filter(
                process=parcours_doctoral_instance.supervision_group
            ).select_related('person')

            if cc_promoteurs:
                for promoter in actors.filter(type=ActorType.PROMOTER.name):
                    cc_list.add(cls._format_email(promoter))

            if cc_membres_ca:
                for ca_member in actors.filter(type=ActorType.CA_MEMBER.name):
                    cc_list.add(cls._format_email(ca_member))

        if cc_jury:
            jury_members = JuryMember.objects.select_related(
                'promoter__person',
                'person',
            ).filter(parcours_doctoral=parcours_doctoral_instance)

            for jury_member in jury_members:
                jury_member_info = cls.get_jury_member_info(jury_member=jury_member)
                cc_list.add(cls._format_email_jury_member(jury_member_info=jury_member_info))

        if cc_list:
            email_message['Cc'] = ','.join(cc_list)

        EmailNotificationHandler.create(email_message, person=parcours_doctoral_instance.student)

        return email_message

    @classmethod
    def _get_parcours_doctoral_title_translation(cls, parcours_doctoral: ParcoursDoctoralModel):
        """Populate the translations of parcours_doctoral title and lazy return them"""
        # Create a dict to cache the translations of the parcours_doctoral title
        parcours_doctoral_title = {
            settings.LANGUAGE_CODE_EN: parcours_doctoral.training.title_english,
            settings.LANGUAGE_CODE_FR: parcours_doctoral.training.title,
        }

        # Return a lazy proxy which, when evaluated to string, return the correct translation given the current language
        return lazy(lambda: parcours_doctoral_title[get_language()], str)()

    @classmethod
    def get_common_tokens(cls, parcours_doctoral: ParcoursDoctoralModel):
        """Return common tokens about a submission"""
        return {
            "student_first_name": parcours_doctoral.student.first_name,
            "student_last_name": parcours_doctoral.student.last_name,
            "training_title": cls._get_parcours_doctoral_title_translation(parcours_doctoral),
            "parcours_doctoral_link_front": get_parcours_doctoral_link_front(parcours_doctoral.uuid),
            "parcours_doctoral_link_back": get_parcours_doctoral_link_back(parcours_doctoral.uuid),
        }

    @classmethod
    def _format_email(cls, actor: ParcoursDoctoralSupervisionActor):
        return "{a.first_name} {a.last_name} <{a.email}>".format(a=actor)

    @classmethod
    def _format_email_jury_member(cls, jury_member_info: NotificationMixin.JuryMemberInfo):
        return "%(first_name)s %(last_name)s <%(email)s>" % jury_member_info

    @classmethod
    def envoyer_signatures(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        groupe_de_supervision: GroupeDeSupervision,
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

    @classmethod
    def renvoyer_invitation(cls, parcours_doctoral: ParcoursDoctoral, membre: SignataireIdentity):
        # Charger le membre et vérifier qu'il est externe et déjà invité
        actor = ParcoursDoctoralSupervisionActor.objects.filter(
            uuid=membre.uuid,
            person_id=None,
            last_state=SignatureState.INVITED.name,
        ).first()
        if not actor:
            raise SignataireNonTrouveException

        # Réinitiliser l'état afin de mettre à jour le token
        actor.switch_state(SignatureState.INVITED)
        actor.refresh_from_db()

        # Tokens communs
        common_tokens = cls.get_common_tokens(parcours_doctoral)

        # Envoyer aux acteurs n'ayant pas répondu
        tokens = {
            **common_tokens,
            "signataire_first_name": actor.first_name,
            "signataire_last_name": actor.last_name,
            "signataire_role": actor.get_type_display(),
            "parcours_doctoral_link_front": cls._lien_invitation_externe(parcours_doctoral, actor),
        }
        email_message = generate_email(
            PARCOURS_DOCTORAL_EMAIL_SIGNATURE_REQUESTS_ACTOR,
            actor.language,
            tokens,
            recipients=[actor.email],
        )
        EmailNotificationHandler.create(email_message)

    @classmethod
    def _lien_invitation_externe(cls, parcours_doctoral, actor):
        return get_parcours_doctoral_link_front(
            uuid=parcours_doctoral.entity_id.uuid,
            tab='public/supervision/',
        ) + get_signing_token(actor)

    @classmethod
    def notifier_suppression_membre(
        cls,
        parcours_doctoral: ParcoursDoctoral,
        signataire_id: 'SignataireIdentity',
    ) -> None:
        # Notifier uniquement si le signataire a déjà signé
        parcours_doctoral_instance = ParcoursDoctoralModel.objects.get(uuid=parcours_doctoral.entity_id.uuid)
        actor = parcours_doctoral_instance.supervision_group.actors.select_related('person').get(
            uuid=signataire_id.uuid
        )
        if actor.state in [SignatureState.APPROVED.name, SignatureState.DECLINED.name]:
            email_message = generate_email(
                PARCOURS_DOCTORAL_EMAIL_MEMBER_REMOVED,
                actor.language,
                {
                    **cls.get_common_tokens(parcours_doctoral_instance),
                    "actor_first_name": actor.first_name,
                    "actor_last_name": actor.last_name,
                },
                recipients=[actor.email],
            )
            EmailNotificationHandler.create(email_message, person=actor.person_id and actor.person)
