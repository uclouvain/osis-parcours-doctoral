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

from base.models.entity_version import (
    PEDAGOGICAL_ENTITY_ADDED_EXCEPTIONS,
    EntityVersion,
)
from base.models.enums.entity_type import PEDAGOGICAL_ENTITY_TYPES
from django.conf import settings
from django.db.models import Func, Q
from django.utils import translation
from django.utils.translation import gettext_lazy as _

FORMATTED_EMAIL_FOR_HISTORY = """{sender_label} : {sender}
{recipient_label} : {recipient}
{cc}{subject_label} : {subject}

{message}"""


def get_message_to_historize(message: EmailMessage) -> dict:
    """
    Get the message to be saved in the history.
    """
    plain_text_content = ""
    for part in message.walk():
        # Mail payload is decoded to bytes then decode to utf8
        if part.get_content_type() == "text/plain":
            plain_text_content = part.get_payload(decode=True).decode(settings.DEFAULT_CHARSET)

    format_args = {
        'sender_label': _("Sender"),
        'recipient_label': _("Recipient"),
        'subject_label': _("Subject"),
        'sender': message.get("From"),
        'recipient': message.get("To"),
        'cc': "CC : {}\n".format(message.get("Cc")) if message.get("Cc") else '',
        'subject': message.get("Subject"),
        'message': plain_text_content,
    }

    with translation.override(settings.LANGUAGE_CODE_FR):
        message_fr = FORMATTED_EMAIL_FOR_HISTORY.format(**format_args)
    with translation.override(settings.LANGUAGE_CODE_EN):
        message_en = FORMATTED_EMAIL_FOR_HISTORY.format(**format_args)

    return {
        settings.LANGUAGE_CODE_FR: message_fr,
        settings.LANGUAGE_CODE_EN: message_en,
    }


def get_entities_with_descendants_ids(entities_acronyms):
    """
    From a list of pedagogical entities acronyms, get a set of ids of the entities and their descendants.
    :param entities_acronyms: A list of acronyms of pedagogical entities
    :return: A set of entities ids
    """
    if entities_acronyms:
        cte = (
            EntityVersion.objects.filter(acronym__in=entities_acronyms)
            .filter(Q(entity_type__in=PEDAGOGICAL_ENTITY_TYPES) | Q(acronym__in=PEDAGOGICAL_ENTITY_ADDED_EXCEPTIONS))
            .with_parents()
        )
        qs = cte.queryset().with_cte(cte).annotate(level=Func('parents', function='cardinality'))
        return set(qs.values_list('entity_id', flat=True))
    return set()
