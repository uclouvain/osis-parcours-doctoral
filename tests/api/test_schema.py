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
import difflib
import filecmp
import sys
import unittest
from unittest import SkipTest

from django.core.files.temp import NamedTemporaryFile
from django.core.management import ManagementUtility, call_command
from django.test import TestCase


class ApiSchemaTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        # Only execute if tests are launched globally
        argv = sys.argv
        utility = ManagementUtility(argv)
        test_command = utility.fetch_command('test')
        parser = test_command.create_parser(argv[0], argv[1])

        options = parser.parse_args(argv[2:])
        if not options.args or options.args[0].split('.')[0] != 'parcours_doctoral':
            raise SkipTest("Not testing parcours_doctoral directly, do not test schema")
        super().setUpClass()

    def test_api_schema_matches_generation(self):
        with NamedTemporaryFile(mode='w+') as temp:
            call_command(
                'compilemessages',
                verbosity=0,
                locale='fr_BE',
                ignore_patterns=[
                    '.git',
                    '*/.git',
                    '.*',
                    '*/.*',
                    '__pycache__',
                    'node_modules',
                    'uploads',
                    'ddd',
                    '*/ddd',
                    'infrastructure',
                    '*/infrastructure',
                    '*/migrations',
                    '*/static',
                    '*/tests',
                    '*/templates',
                ],
            )
            call_command(
                'spectacular',
                urlconf='parcours_doctoral.api.url_v1',
                generator_class='parcours_doctoral.api.schema.ParcoursDoctoralSchemaGenerator',
                file=temp.name,
            )
            if not filecmp.cmp('parcours_doctoral/schema.yml', temp.name, shallow=False):
                with open('parcours_doctoral/schema.yml', 'r') as schema_file:
                    schema_lines = schema_file.readlines()
                with open(temp.name, 'r') as new_schema_file:
                    new_schema_lines = new_schema_file.readlines()
                self.fail(
                    "Schema has not been re-generated:\n\n"
                    + ''.join(
                        difflib.unified_diff(
                            schema_lines,
                            new_schema_lines,
                            fromfile='schema.yml',
                            tofile='generated_schema.yml',
                        )
                    )
                )
