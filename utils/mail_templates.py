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
from typing import Optional, Union

from osis_mail_template.models import MailTemplate

from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.mail_templates import PARCOURS_DOCTORAL_EMAIL_GENERIC
from parcours_doctoral.mail_templates.confirmation_paper import (
    PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT,
)
from parcours_doctoral.models import ParcoursDoctoral
from parcours_doctoral.models.cdd_mail_template import (
    ALLOWED_CUSTOM_IDENTIFIERS,
    CddMailTemplate,
)


def get_mail_templates_from_doctorate(parcours_doctoral: ParcoursDoctoral):
    allowed_templates = [PARCOURS_DOCTORAL_EMAIL_GENERIC]
    if parcours_doctoral.status == ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name:
        allowed_templates.append(PARCOURS_DOCTORAL_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT)
    return allowed_templates


def get_email_templates_by_language(identifier: str, management_entity_id: int):
    """
    Return a dictionary containing the specific email templates by language if any, otherwise the generic ones, else
    an empty dictionary.

    :param identifier: the identifier of the template
    :param management_entity_id: the id of the management entity of the cdd linked to the specific email templates

    :rtype: dict[str, CddMailTemplate | MailTemplate]
    """
    mail_templates: list[Union[CddMailTemplate, MailTemplate]] = []

    # Custom email templates
    if identifier in ALLOWED_CUSTOM_IDENTIFIERS:
        mail_templates = CddMailTemplate.objects.filter(identifier=identifier, cdd_id=management_entity_id)

    # Base version of the email templates
    if not mail_templates:
        mail_templates = MailTemplate.objects.filter(identifier=identifier)

    return {mail_template.language: mail_template for mail_template in mail_templates}


def get_email_template(identifier: str, language: str, management_entity_id: int):
    """
    Return the specific email template if any, otherwise the generic one, else None.

    :param identifier: the identifier of the template
    :param language: the language of the template
    :param management_entity_id: the id of the management entity of the cdd linked to the specific email template

    :rtype: CddMailTemplate | MailTemplate | None
    """
    mail_template: Optional[Union[CddMailTemplate, MailTemplate]] = None

    # Custom email template
    if identifier in ALLOWED_CUSTOM_IDENTIFIERS:
        mail_template = CddMailTemplate.objects.filter(
            identifier=identifier,
            cdd_id=management_entity_id,
            language=language,
        ).first()

    # Base version of the email template
    if not mail_template:
        mail_template = MailTemplate.objects.filter(identifier=identifier, language=language).first()

    return mail_template
