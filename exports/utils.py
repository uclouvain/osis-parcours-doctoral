# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################

from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import override
from osis_document.api.utils import change_remote_metadata
from weasyprint import HTML

from osis_common.utils.url_fetcher import django_url_fetcher


def get_pdf_from_template(template_name, stylesheets, context) -> bytes:
    """
    Generate a PDF given a template name, stylesheets and context and returns it as bytes
    """
    html_string = render_to_string(template_name, context)
    html = HTML(string=html_string, url_fetcher=django_url_fetcher, base_url="file:")
    return html.write_pdf(presentational_hints=True, stylesheets=stylesheets)


def parcours_doctoral_generate_pdf(
    parcours_doctoral,
    template,
    filename,
    context=None,
    stylesheets=None,
    author='',
    language=None,
):
    """
    Generate a pdf.

    :param parcours_doctoral: ParcoursDoctoral to generate a PDF for
    :param template: Name of the template used to generate PDF
    :param context: Extra context variables given to the template
    :param filename: Filename
    :param stylesheets: Stylesheets
    :param author: Author
    :return: Writing token of the saved file
    """
    from osis_document.utils import save_raw_content_remotely

    current_language = translation.get_language()
    try:
        if language is not None:
            translation.activate(language)
        result = get_pdf_from_template(
            template,
            stylesheets or [],
            {'parcours_doctoral': parcours_doctoral, **(context or {})},
        )
    finally:
        translation.activate(current_language)

    token = save_raw_content_remotely(result, filename, 'application/pdf')
    if author:
        change_remote_metadata(token=token, metadata={'author': author})
    return token


def generate_temporary_pdf(
    parcours_doctoral,
    template,
    filename,
    context=None,
    stylesheets=None,
    language=None,
):
    """
    Generate a temporary pdf.

    :param parcours_doctoral: ParcoursDoctoral to generate a PDF for
    :param template: Name of the template used to generate PDF
    :param context: Extra context variables given to the template
    :param filename: Filename
    :param stylesheets: Stylesheets
    :return: URL of the temporary file
    """
    from osis_document.utils import get_file_url, save_raw_content_remotely

    with override(language or translation.get_language()):
        result = get_pdf_from_template(
            template,
            stylesheets or [],
            {'parcours_doctoral': parcours_doctoral, **(context or {})},
        )

    token = save_raw_content_remotely(result, filename, 'application/pdf')

    return get_file_url(token)
