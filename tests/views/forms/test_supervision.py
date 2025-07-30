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
from unittest.mock import ANY, Mock, patch

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from osis_signature.enums import SignatureState
from osis_signature.models import StateHistory

from admission.tests.factories.person import InternalPersonFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import ExternalPersonFactory, PersonFactory
from base.tests.factories.tutor import TutorFactory
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ENTITY_CDE
from parcours_doctoral.forms.supervision import ACTOR_EXTERNAL, EXTERNAL_FIELDS
from parcours_doctoral.models import ActorType
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.roles import AdreSecretaryRoleFactory
from parcours_doctoral.tests.factories.supervision import (
    CaMemberFactory,
    ExternalPromoterFactory,
    PromoterFactory,
    _ProcessFactory,
)
from reference.tests.factories.country import CountryFactory


@override_settings(ADMISSION_TOKEN_EXTERNAL='api-token-external')
class SupervisionTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        # First entity
        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)

        # Create parcours_doctoral
        cls.parcours_doctoral = ParcoursDoctoralFactory(
            supervision_group=_ProcessFactory(),
        )

        # Users
        cls.program_manager_user = AdreSecretaryRoleFactory().person.user

        cls.promoter = PromoterFactory(process=cls.parcours_doctoral.supervision_group)
        cls.ca_member = CaMemberFactory(process=cls.parcours_doctoral.supervision_group)
        cls.external_member = ExternalPromoterFactory(process=cls.parcours_doctoral.supervision_group)

        cls.country = CountryFactory()

        cls.person = InternalPersonFactory(global_id='00005789')
        TutorFactory(person=cls.person)

        cls.external_person = ExternalPersonFactory()

        # Urls
        cls.update_url = reverse('parcours_doctoral:update:supervision', args=[cls.parcours_doctoral.uuid])
        cls.detail_url = reverse('parcours_doctoral:supervision', args=[cls.parcours_doctoral.uuid])

    def setUp(self):
        # Mock documents
        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.get_remote_metadata",
            return_value={"name": "myfile", "mimetype": "application/pdf", "size": 1},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.confirm_remote_upload",
            side_effect=lambda token, *args, **kwargs: token,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch(
            "osis_document.contrib.fields.FileField._confirm_multiple_upload",
            side_effect=lambda _, value, __: value,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_should_detail_supervision_member(self):
        self.client.force_login(user=self.program_manager_user)
        response = self.client.get(self.update_url)
        self.assertTemplateUsed(response, 'parcours_doctoral/details/supervision.html')
        # Display the signatures
        self.assertContains(response, self.promoter.person.last_name)

    def test_should_add_supervision_member_error(self):
        self.client.force_login(user=self.program_manager_user)
        response = self.client.post(self.update_url, {'type': ActorType.CA_MEMBER.name})
        self.assertEqual(response.status_code, 200)
        self.assertIn('__all__', response.context['add_form'].errors)

    def test_should_add_ca_member_ok(self):
        self.client.force_login(user=self.program_manager_user)
        data = {
            'type': ActorType.CA_MEMBER.name,
            'internal_external': "INTERNAL",
            'person': self.person.global_id,
            'email': "test@test.fr",
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 302)

    def test_should_add_supervision_member_error_already_in(self):
        self.client.force_login(user=self.program_manager_user)
        response = self.client.post(self.update_url, {'type': ActorType.PROMOTER.name})
        self.assertEqual(response.status_code, 200)
        self.assertIn('__all__', response.context['add_form'].errors)

    def test_should_add_promoter_ok(self):
        self.client.force_login(user=self.program_manager_user)

        data = {
            'type': ActorType.PROMOTER.name,
            'internal_external': "INTERNAL",
            'person': self.person.global_id,
            'email': "test@test.fr",
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 302)

    def test_should_add_promoter_external_error(self):
        self.client.force_login(user=self.program_manager_user)
        data = {
            'type': ActorType.PROMOTER.name,
            'internal_external': ACTOR_EXTERNAL,
            'email': "test@test.fr",
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(EXTERNAL_FIELDS) - 1, len(response.context['add_form'].errors))
        self.assertIn('prenom', response.context['add_form'].errors)

    def test_should_add_promoter_external_ok(self):
        self.client.force_login(user=self.program_manager_user)
        external_data = {
            'prenom': 'John',
            'nom': 'Doe',
            'email': 'john@example.org',
            'est_docteur': True,
            'institution': 'ins',
            'ville': 'mons',
            'pays': self.country.iso_code,
            'langue': 'fr-be',
        }
        data = {
            'type': ActorType.PROMOTER.name,
            'internal_external': ACTOR_EXTERNAL,
            'person': self.person.global_id,
            **external_data,
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 302)

    def test_should_remove_promoter(self):
        self.client.force_login(user=self.program_manager_user)
        url = resolve_url(
            "parcours_doctoral:update:remove-actor",
            uuid=str(self.parcours_doctoral.uuid),
            type=ActorType.PROMOTER.name,
            uuid_membre=str(self.promoter.uuid),
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_should_remove_supervision_member_error(self):
        self.client.force_login(user=self.program_manager_user)
        url = resolve_url(
            "parcours_doctoral:update:remove-actor",
            uuid=str(self.parcours_doctoral.uuid),
            type=ActorType.PROMOTER.name,
            uuid_membre=str(self.ca_member.uuid),
        )
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 404)

    def test_should_edit_external_supervision_member(self):
        self.client.force_login(user=self.program_manager_user)
        url = resolve_url(
            "parcours_doctoral:update:edit-external-member",
            uuid=str(self.parcours_doctoral.uuid),
            uuid_membre=str(self.external_member.uuid),
        )
        external_data = {
            f'member-{self.external_member.uuid}-{k}': v
            for k, v in {
                'prenom': 'John',
                'nom': 'Doe',
                'email': 'john@example.org',
                'est_docteur': True,
                'institution': 'ins',
                'ville': 'mons',
                'pays': self.country.iso_code,
                'langue': 'fr-be',
            }.items()
        }
        response = self.client.post(url, external_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.detail_url, target_status_code=302)
        self.external_member.refresh_from_db()
        self.assertEqual(self.external_member.last_name, 'Doe')
        self.assertEqual(self.external_member.email, 'john@example.org')

    def test_should_not_remove_ca_member_if_not_found(self):
        self.client.force_login(user=self.program_manager_user)
        url = resolve_url(
            "parcours_doctoral:update:remove-actor",
            uuid=str(self.parcours_doctoral.uuid),
            type=ActorType.CA_MEMBER.name,
            uuid_membre="34eab30c-27e3-40db-b92e-0b51546a2448",
        )
        response = self.client.get(url, {})
        self.assertEqual(response.status_code, 404)

    def test_should_not_remove_promoter_if_not_found(self):
        self.client.force_login(user=self.program_manager_user)

        url = resolve_url(
            "parcours_doctoral:update:remove-actor",
            uuid=str(self.parcours_doctoral.uuid),
            type=ActorType.PROMOTER.name,
            uuid_membre="34eab30c-27e3-40db-b92e-0b51546a2448",
        )
        response = self.client.get(url, {})
        self.assertEqual(response.status_code, 404)

    def test_should_approval_by_pdf_redirect_without_errors(self, *args):
        self.client.force_login(user=self.program_manager_user)
        StateHistory.objects.create(
            actor=self.promoter,
            state=SignatureState.INVITED.name,
        )

        url = resolve_url("parcours_doctoral:update:approve-by-pdf", uuid=str(self.parcours_doctoral.uuid))
        response = self.client.post(
            url,
            {
                'uuid_membre': self.promoter.uuid,
                'pdf_0': '34eab30c-27e3-40db-b92e-0b51546a2448',
            },
        )
        expected_url = resolve_url("parcours_doctoral:supervision", uuid=str(self.parcours_doctoral.uuid))
        self.assertRedirects(response, expected_url, target_status_code=302)
        self.promoter.refresh_from_db()
        self.assertTrue(self.promoter.pdf_from_candidate)
        self.assertEqual(self.promoter.state, SignatureState.APPROVED.name)

    def test_should_approval_by_pdf_redirect_with_errors(self):
        self.client.force_login(user=self.program_manager_user)
        url = resolve_url("parcours_doctoral:update:approve-by-pdf", uuid=str(self.parcours_doctoral.uuid))
        response = self.client.post(url, {})
        self.assertRedirects(response, self.detail_url, target_status_code=302)

    def test_should_set_reference_promoter(self):
        self.client.force_login(user=self.program_manager_user)
        url = resolve_url(
            "parcours_doctoral:update:set-reference-promoter",
            uuid=str(self.parcours_doctoral.uuid),
            uuid_promoteur=self.promoter.uuid,
        )
        response = self.client.post(url, {})
        self.assertRedirects(response, self.detail_url, target_status_code=302)
        self.promoter.refresh_from_db()
        self.assertTrue(self.promoter.is_reference_promoter)

    def test_should_not_add_promoter_with_an_external_account(self):
        self.client.force_login(user=self.program_manager_user)

        data = {
            'type': ActorType.PROMOTER.name,
            'internal_external': "INTERNAL",
            'person': self.external_person.global_id,
            'email': "test@test.fr",
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('__all__', response.context['add_form'].errors)

    def test_should_not_add_ca_member_with_an_external_account(self):
        self.client.force_login(user=self.program_manager_user)

        data = {
            'type': ActorType.CA_MEMBER.name,
            'internal_external': "INTERNAL",
            'person': self.external_person.global_id,
            'email': "test@test.fr",
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('__all__', response.context['add_form'].errors)
