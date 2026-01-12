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
from django.conf import settings
from django.db.models import Case, QuerySet, Value, When
from django.utils.translation import gettext_lazy, override, pgettext_lazy
from osis_notification.contrib.handlers import EmailNotificationHandler
from osis_notification.contrib.notification import EmailNotification

from parcours_doctoral.ddd.jury.domain.model.enums import (
    ROLES_MEMBRES_JURY,
    RoleJury,
    TitreMembre,
)
from parcours_doctoral.ddd.recevabilite.domain.service.i_notification import (
    INotification,
)
from parcours_doctoral.infrastructure.mixins.notification import NotificationMixin
from parcours_doctoral.mail_templates.admissibility import (
    PARCOURS_DOCTORAL_EMAIL_ADMISSIBILITY_JURY_INVITATION,
)
from parcours_doctoral.models import JuryActor, ParcoursDoctoral
from parcours_doctoral.utils.mail_templates import get_email_templates_by_language
from parcours_doctoral.utils.url import (
    get_parcours_doctoral_link_back,
    get_parcours_doctoral_link_front,
)


class Notification(NotificationMixin, INotification):
    @classmethod
    def get_doctorate(cls, doctorate_uuid) -> ParcoursDoctoral:
        """Return the doctorate"""
        return ParcoursDoctoral.objects.select_related(
            'student',
            'training',
            'current_admissibility',
        ).get(uuid=doctorate_uuid)

    @classmethod
    def get_jury_members(cls, jury_group_id, roles: set[str] | None = None) -> QuerySet[JuryActor]:
        """Return the jury members for a specific group for some roles"""
        return (
            JuryActor.objects.filter(
                process_id=jury_group_id,
                role__in=roles or [RoleJury.PRESIDENT.name, RoleJury.SECRETAIRE.name],
            )
            .annotate(
                formatted_title=Case(
                    When(person__tutor__isnull=False, then=Value('Dr.')),
                    When(title=TitreMembre.PROFESSEUR.name, then=Value('Prof.')),
                    When(title=TitreMembre.DOCTEUR.name, then=Value('Dr.')),
                )
            )
            .select_related('person')
        )

    @classmethod
    def get_common_tokens(
        cls,
        doctorate: ParcoursDoctoral,
        jury_members: QuerySet[JuryActor] | None,
    ) -> dict:
        """Return common tokens about a doctorate"""
        jury_members_by_role = {
            jury_member.role: jury_member
            for jury_member in jury_members
            if jury_member.role in {RoleJury.PRESIDENT.name, RoleJury.SECRETAIRE.name}
        }
        current_admissibility = getattr(doctorate, 'current_admissibility', None)
        return {
            'student_first_name': doctorate.student.first_name,
            'student_last_name': doctorate.student.last_name,
            'training_title': cls._get_parcours_doctoral_title_translation(doctorate),
            'parcours_doctoral_link_front': get_parcours_doctoral_link_front(doctorate.uuid),
            'parcours_doctoral_link_back': get_parcours_doctoral_link_back(doctorate.uuid),
            'parcours_doctoral_link_front_admissibility_minutes': get_parcours_doctoral_link_front(
                doctorate.uuid,
                f'admissibility-minutes/{current_admissibility.uuid}' if current_admissibility else 'admissibility',
            ),
            'parcours_doctoral_link_front_thesis_distribution_authorisation': get_parcours_doctoral_link_front(
                doctorate.uuid,
                'thesis-distribution-authorisation',
            ),
            'admissibility_decision_date': (
                cls._format_date(current_admissibility.decision_date) if current_admissibility else ''
            ),
            'reference': doctorate.reference,
            'student_reference': {
                'F': pgettext_lazy('F', 'the PhD student'),
                'H': pgettext_lazy('H', 'the PhD student'),
            }.get(doctorate.student.gender)
            or pgettext_lazy('X', 'the PhD student'),
            'student_personal_pronoun': {
                'F': gettext_lazy('she'),
                'H': gettext_lazy('he'),
            }.get(doctorate.student.gender)
            or gettext_lazy('he'),
            'jury_president': cls._format_actor(jury_members_by_role.get(RoleJury.PRESIDENT.name)),
            'jury_secretary': cls._format_actor(jury_members_by_role.get(RoleJury.SECRETAIRE.name)),
        }

    @classmethod
    def _format_actor(cls, jury_actor: JuryActor | None):
        """Format the name of the actor"""
        if not jury_actor:
            return ''

        if jury_actor.formatted_title:
            return f'{jury_actor.formatted_title} {jury_actor.first_name} {jury_actor.last_name}'

        return f'{jury_actor.first_name} {jury_actor.last_name}'

    @classmethod
    def inviter_membres_jury(cls, parcours_doctoral_uuid: str) -> None:
        doctorate = cls.get_doctorate(doctorate_uuid=parcours_doctoral_uuid)

        jury_members = cls.get_jury_members(jury_group_id=doctorate.jury_group_id, roles=ROLES_MEMBRES_JURY)

        common_tokens = cls.get_common_tokens(
            doctorate=doctorate,
            jury_members=jury_members,
        )

        email_templates = get_email_templates_by_language(
            identifier=PARCOURS_DOCTORAL_EMAIL_ADMISSIBILITY_JURY_INVITATION,
            management_entity_id=doctorate.training.management_entity_id,
        )

        for jury_member in jury_members:
            current_language = jury_member.language or settings.LANGUAGE_CODE
            related_person = jury_member.person if jury_member.person_id else None

            tokens = {
                **common_tokens,
                'jury_member_first_name': jury_member.first_name,
                'jury_member_last_name': jury_member.last_name,
            }

            email_template = email_templates[current_language]

            with override(current_language):
                email_notification = EmailNotification(
                    recipient=related_person or jury_member.email,
                    subject=email_template.render_subject(tokens),
                    html_content=email_template.body_as_html(tokens),
                    plain_text_content=email_template.body_as_plain(tokens),
                )

            jury_member_email_message = EmailNotificationHandler.build(email_notification)
            EmailNotificationHandler.create(jury_member_email_message, person=related_person)
