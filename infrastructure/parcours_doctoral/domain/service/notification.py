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

from email.message import EmailMessage

from django.conf import settings
from django.shortcuts import resolve_url
from django.utils.functional import lazy
from django.utils.translation import get_language

from admission.models import SupervisionActor
from admission.models.enums.actor_type import ActorType
from parcours_doctoral.ddd.domain.model.groupe_de_supervision import SignataireIdentity, GroupeDeSupervision
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ParcoursDoctoral
from parcours_doctoral.ddd.domain.service.i_notification import INotification
from osis_mail_template.utils import transform_html_to_text
from osis_notification.contrib.handlers import EmailNotificationHandler
from osis_notification.contrib.notification import EmailNotification

from parcours_doctoral.models.parcours_doctoral import ParcoursDoctoral as ParcoursDoctoralModel


class Notification(INotification):
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
        actors = SupervisionActor.objects.filter(process=parcours_doctoral_instance.supervision_group).select_related('person')
        cc_list = []
        if cc_promoteurs:
            for promoter in actors.filter(type=ActorType.PROMOTER.name):
                cc_list.append(cls._format_email(promoter))
        if cc_membres_ca:
            for ca_member in actors.filter(type=ActorType.CA_MEMBER.name):
                cc_list.append(cls._format_email(ca_member))
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
            "candidate_first_name": parcours_doctoral.student.first_name,
            "candidate_last_name": parcours_doctoral.student.last_name,
            "training_title": cls._get_parcours_doctoral_title_translation(parcours_doctoral),
            "admission_link_front": settings.ADMISSION_FRONTEND_LINK.format(context='parcours_doctoral', uuid=parcours_doctoral.uuid),
            "admission_link_back": "{}{}".format(
                settings.ADMISSION_BACKEND_LINK_PREFIX,
                resolve_url('admission:parcours_doctoral:project', uuid=parcours_doctoral.uuid),
            ),
        }

    @classmethod
    def _format_email(cls, actor: SupervisionActor):
        return "{a.first_name} {a.last_name} <{a.email}>".format(a=actor)

    @classmethod
    def envoyer_signatures(cls, parcours_doctoral: ParcoursDoctoral, groupe_de_supervision: GroupeDeSupervision) -> None:
        admission = PropositionProxy.objects.get(uuid=proposition.entity_id.uuid)

        # Création de la tâche de génération du document
        task = AsyncTask.objects.create(
            name=_("Exporting %(reference)s to PDF") % {'reference': admission.reference},
            description=_("Exporting the admission information to PDF"),
            person=admission.candidate,
            time_to_live=5,
        )
        AdmissionTask.objects.create(
            task=task,
            admission=admission,
            type=AdmissionTask.TaskType.ARCHIVE.name,
        )

        # Tokens communs
        candidat = Person.objects.get(global_id=proposition.matricule_candidat)
        common_tokens = cls.get_common_tokens(proposition, candidat)
        common_tokens["admission_link_back"] = "{}{}".format(
            settings.ADMISSION_BACKEND_LINK_PREFIX,
            resolve_url('admission:doctorate:supervision', uuid=proposition.entity_id.uuid),
        )
        common_tokens["admission_link_front"] = "{}{}".format(
            common_tokens["admission_link_front"],
            'supervision',
        )
        actor_list = SupervisionActor.objects.filter(process=admission.supervision_group).select_related('person')

        # Envoyer aux gestionnaires CDD
        for manager in get_admission_cdd_managers(admission.training.education_group_id):
            with translation.override(manager.language):
                content = (
                    _(
                        '<a href="%(admission_link_back)s">%(reference)s</a> - '
                        '%(candidate_first_name)s %(candidate_last_name)s requested '
                        'signatures for %(training_title)s'
                    )
                    % common_tokens
                )
                web_notification = WebNotification(recipient=manager, content=str(content))
            WebNotificationHandler.create(web_notification)

        # Envoyer au doctorant
        with translation.override(candidat.language):
            actor_list_str = [
                f"{actor.first_name} {actor.last_name} ({actor.get_type_display()})" for actor in actor_list
            ]
        email_message = generate_email(
            ADMISSION_EMAIL_SIGNATURE_REQUESTS_CANDIDATE,
            candidat.language,
            {
                **common_tokens,
                "actors_as_list_items": '<li></li>'.join(actor_list_str),
                "actors_comma_separated": ', '.join(actor_list_str),
            },
            recipients=[candidat.email],
        )
        EmailNotificationHandler.create(email_message, person=candidat)

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
                tokens["admission_link_front"] = cls._lien_invitation_externe(proposition, actor)
            email_message = generate_email(
                ADMISSION_EMAIL_SIGNATURE_REQUESTS_ACTOR,
                actor.language,
                tokens,
                recipients=[actor.email],
            )
            EmailNotificationHandler.create(email_message, person=actor.person_id and actor.person)

    @classmethod
    def renvoyer_invitation(cls, parcours_doctoral: ParcoursDoctoral, membre: SignataireIdentity):
        # Charger le membre et vérifier qu'il est externe et déjà invité
        actor = SupervisionActor.objects.filter(
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
        candidat = Person.objects.get(global_id=proposition.matricule_candidat)
        common_tokens = cls.get_common_tokens(proposition, candidat)

        # Envoyer aux acteurs n'ayant pas répondu
        tokens = {
            **common_tokens,
            "signataire_first_name": actor.first_name,
            "signataire_last_name": actor.last_name,
            "signataire_role": actor.get_type_display(),
            "admission_link_front": cls._lien_invitation_externe(proposition, actor),
        }
        email_message = generate_email(
            ADMISSION_EMAIL_SIGNATURE_REQUESTS_ACTOR,
            actor.language,
            tokens,
            recipients=[actor.email],
        )
        EmailNotificationHandler.create(email_message)

    @classmethod
    def _lien_invitation_externe(cls, proposition, actor):
        url = settings.ADMISSION_FRONTEND_LINK.format(context='public/doctorate', uuid=proposition.entity_id.uuid)
        return url + f"external-approval/{get_signing_token(actor)}"

    @classmethod
    def notifier_suppression_membre(cls, parcours_doctoral: ParcoursDoctoral, signataire_id: 'SignataireIdentity') -> None:
        # Notifier uniquement si le signataire a déjà signé
        admission = PropositionProxy.objects.get(uuid=proposition.entity_id.uuid)
        actor = admission.supervision_group.actors.select_related('person').get(uuid=signataire_id.uuid)
        if actor.state in [SignatureState.APPROVED.name, SignatureState.DECLINED.name]:
            candidat = Person.objects.get(global_id=proposition.matricule_candidat)
            email_message = generate_email(
                ADMISSION_EMAIL_MEMBER_REMOVED,
                actor.language,
                {
                    **cls.get_common_tokens(proposition, candidat),
                    "actor_first_name": actor.first_name,
                    "actor_last_name": actor.last_name,
                },
                recipients=[actor.email],
            )
            EmailNotificationHandler.create(email_message, person=actor.person_id and actor.person)
