# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.shortcuts import resolve_url
from rest_framework import status
from rest_framework.test import APITestCase

from base.tests.factories.entity import EntityFactory
from base.tests.factories.person import PersonFactory
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.models import JuryActor, ParcoursDoctoral
from parcours_doctoral.tests.factories.jury import ExternalJuryActorFactory
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.roles import StudentRoleFactory
from parcours_doctoral.tests.factories.supervision import (
    CaMemberFactory,
    PromoterFactory,
)
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.language import FrenchLanguageFactory


class JuryApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Data
        doctoral_commission = EntityFactory()
        cls.parcours_doctoral = ParcoursDoctoralFactory(
            training__management_entity=doctoral_commission,
            thesis_proposed_title='Thesis title',
        )
        cls.updated_data = {
            'titre_propose': 'titre api',
            'formule_defense': 'DEUX_TEMPS',
            'date_indicative': '2023-12-25',
            'langue_redaction': FrenchLanguageFactory().pk,
            'langue_soutenance': 'FRENCH',
            'commentaire': 'commentaire',
        }
        # Targeted url
        cls.base_namespace = "parcours_doctoral_api_v1:jury-preparation"
        cls.url = resolve_url(cls.base_namespace, uuid=cls.parcours_doctoral.uuid)
        # Create an parcours_doctoral supervision group
        promoter = PromoterFactory()
        reference_promoter = PromoterFactory(process=promoter.process, is_reference_promoter=True)
        committee_member = CaMemberFactory(process=promoter.process)
        cls.parcours_doctoral.supervision_group = promoter.process
        cls.parcours_doctoral.save()
        # Users
        cls.student = cls.parcours_doctoral.student
        cls.other_student_user = StudentRoleFactory().person.user
        cls.no_role_user = PersonFactory().user
        cls.promoter_user = promoter.person.user
        cls.reference_promoter_user = reference_promoter.person.user
        cls.other_promoter_user = PromoterFactory().person.user
        cls.committee_member_user = committee_member.person.user
        cls.other_committee_member_user = CaMemberFactory().person.user

    def setUp(self):
        self.parcours_doctoral.status = ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE.name
        self.parcours_doctoral.save()

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.student.user)
        methods_not_allowed = ['delete', 'put', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_jury_get_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_update_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.post(self.url, data=self.updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_get_with_invalid_enrolment_is_forbidden(self):
        in_creation_doctorate = ParcoursDoctoralFactory(
            supervision_group=self.parcours_doctoral.supervision_group,
            student=self.student,
            create_student__with_valid_enrolment=False,
        )

        url = resolve_url(self.base_namespace, uuid=in_creation_doctorate.uuid)

        users = [
            self.promoter_user,
            self.committee_member_user,
            self.student.user,
        ]

        for user in users:
            self.client.force_authenticate(user=user)
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_jury_get_student(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_jury_update_using_api_student(self):
        self.client.force_authenticate(user=self.student.user)
        parcours_doctoral = ParcoursDoctoral.objects.get()
        self.assertEqual(parcours_doctoral.thesis_proposed_title, "Thesis title")

        response = self.client.post(self.url, data=self.updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        parcours_doctoral = ParcoursDoctoral.objects.get()
        self.assertEqual(parcours_doctoral.thesis_proposed_title, "titre api")

        response = self.client.get(self.url, format="json")
        self.assertEqual(response.json()['titre_propose'], "titre api")

    def test_jury_get_other_student(self):
        self.client.force_authenticate(user=self.other_student_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_update_other_student(self):
        self.client.force_authenticate(user=self.other_student_user)
        response = self.client.post(self.url, data=self.updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_get_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_jury_update_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.post(self.url, data=self.updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_update_reference_promoter(self):
        self.client.force_authenticate(user=self.reference_promoter_user)
        response = self.client.post(self.url, data=self.updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_jury_get_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_update_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.post(self.url, data=self.updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_get_committee_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_jury_update_committee_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.post(self.url, data=self.updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)


class JuryMembersListApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Data
        doctoral_commission = EntityFactory()
        country = CountryFactory()
        cls.parcours_doctoral = ParcoursDoctoralFactory(
            training__management_entity=doctoral_commission,
            thesis_proposed_title='Thesis title',
        )
        cls.created_data = {
            'matricule': '',
            'institution': 'institution',
            'autre_institution': 'autre_institution',
            'pays': country.name,
            'nom': 'nom',
            'prenom': 'nouveau prenom',
            'titre': 'DOCTEUR',
            'justification_non_docteur': '',
            'genre': 'AUTRE',
            'email': 'email@example.org',
            'langue': 'FR',
        }
        # Targeted url
        cls.url = resolve_url("parcours_doctoral_api_v1:jury-members-list", uuid=cls.parcours_doctoral.uuid)
        # Create an parcours_doctoral supervision group
        promoter = PromoterFactory()
        reference_promoter = PromoterFactory(process=promoter.process, is_reference_promoter=True)
        committee_member = CaMemberFactory(process=promoter.process)
        cls.parcours_doctoral.supervision_group = promoter.process
        cls.parcours_doctoral.save()
        # Users
        cls.student = cls.parcours_doctoral.student
        cls.other_student_user = StudentRoleFactory().person.user
        cls.no_role_user = PersonFactory().user
        cls.promoter_user = promoter.person.user
        cls.reference_promoter_user = reference_promoter.person.user
        cls.other_promoter_user = PromoterFactory().person.user
        cls.committee_member_user = committee_member.person.user
        cls.other_committee_member_user = CaMemberFactory().person.user

    def setUp(self):
        self.parcours_doctoral.status = ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE.name
        self.parcours_doctoral.save()

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.student.user)
        methods_not_allowed = ['delete', 'put', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_jury_get_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_update_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.post(self.url, data=self.created_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_get_student(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_jury_create_using_api_student(self):
        self.client.force_authenticate(user=self.student.user)
        parcours_doctoral = ParcoursDoctoral.objects.get()
        self.assertEqual(parcours_doctoral.thesis_proposed_title, "Thesis title")

        response = self.client.post(self.url, data=self.created_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        parcours_doctoral = ParcoursDoctoral.objects.get()
        membre = JuryActor.objects.filter(process=parcours_doctoral.jury_group, is_promoter=False).last()
        self.assertEqual(membre.first_name, "nouveau prenom")

        response = self.client.get(self.url, format="json")
        created_member = next((member for member in response.json() if member['uuid'] == str(membre.uuid)), None)
        self.assertIsNotNone(created_member)
        self.assertEqual(created_member['prenom'], "nouveau prenom")

    def test_jury_get_other_student(self):
        self.client.force_authenticate(user=self.other_student_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_post_other_student(self):
        self.client.force_authenticate(user=self.other_student_user)
        response = self.client.post(self.url, data=self.created_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_get_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_jury_post_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.post(self.url, data=self.created_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_post_reference_promoter(self):
        self.client.force_authenticate(user=self.reference_promoter_user)
        response = self.client.post(self.url, data=self.created_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

    def test_jury_get_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_post_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.post(self.url, data=self.created_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_jury_get_committee_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_jury_post_committee_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.post(self.url, data=self.created_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)


class JuryMembersDetailApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Data
        doctoral_commission = EntityFactory()
        country = CountryFactory()
        cls.parcours_doctoral = ParcoursDoctoralFactory(
            training__management_entity=doctoral_commission,
            thesis_proposed_title='Thesis title',
        )
        cls.member = ExternalJuryActorFactory(process=cls.parcours_doctoral.jury_group)
        cls.udpated_data = {
            'matricule': '',
            'institution': 'institution',
            'autre_institution': 'autre_institution',
            'pays': country.name,
            'nom': 'nom',
            'prenom': 'nouveau prenom',
            'titre': 'DOCTEUR',
            'justification_non_docteur': '',
            'genre': 'AUTRE',
            'email': 'email@example.org',
            'langue': 'fr-be',
        }
        cls.updated_role_data = {'role': 'PRESIDENT'}
        # Targeted url
        cls.url = resolve_url(
            "parcours_doctoral_api_v1:jury-member-detail", uuid=cls.parcours_doctoral.uuid, member_uuid=cls.member.uuid
        )
        # Create an parcours_doctoral supervision group
        promoter = PromoterFactory()
        reference_promoter = PromoterFactory(process=promoter.process, is_reference_promoter=True)
        committee_member = CaMemberFactory(process=promoter.process)
        cls.parcours_doctoral.supervision_group = promoter.process
        cls.parcours_doctoral.save()
        # Users
        cls.student = cls.parcours_doctoral.student
        cls.other_student_user = StudentRoleFactory().person.user
        cls.no_role_user = PersonFactory().user
        cls.promoter_user = promoter.person.user
        cls.reference_promoter_user = reference_promoter.person.user
        cls.other_promoter_user = PromoterFactory().person.user
        cls.committee_member_user = committee_member.person.user
        cls.other_committee_member_user = CaMemberFactory().person.user

    def setUp(self):
        self.parcours_doctoral.status = ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE.name
        self.parcours_doctoral.save()

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.student.user)
        methods_not_allowed = ['post']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # GET
    def test_jury_get_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_get_using_api_student(self):
        self.client.force_authenticate(user=self.student.user)
        parcours_doctoral = ParcoursDoctoral.objects.get()
        self.assertEqual(parcours_doctoral.thesis_proposed_title, "Thesis title")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_get_other_student(self):
        self.client.force_authenticate(user=self.other_student_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_get_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_get_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_get_committee_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    # PUT
    def test_jury_put_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.put(self.url, data=self.udpated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_put_using_api_student(self):
        self.client.force_authenticate(user=self.student.user)
        parcours_doctoral = ParcoursDoctoral.objects.get()
        self.assertEqual(parcours_doctoral.thesis_proposed_title, "Thesis title")

        response = self.client.put(self.url, data=self.udpated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        membre = JuryActor.objects.get(uuid=self.member.uuid)
        self.assertEqual(membre.first_name, "nouveau prenom")

    def test_put_other_student(self):
        self.client.force_authenticate(user=self.other_student_user)
        response = self.client.put(self.url, data=self.udpated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_put_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.put(self.url, data=self.udpated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_put_reference_promoter(self):
        self.client.force_authenticate(user=self.reference_promoter_user)
        response = self.client.put(self.url, data=self.udpated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_put_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.put(self.url, data=self.udpated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_put_committee_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.put(self.url, data=self.udpated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    # PATCH
    def test_patch_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.patch(self.url, data=self.updated_role_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_patch_using_api_student(self):
        self.client.force_authenticate(user=self.student.user)
        parcours_doctoral = ParcoursDoctoral.objects.get()
        self.assertEqual(parcours_doctoral.thesis_proposed_title, "Thesis title")

        response = self.client.patch(self.url, data=self.updated_role_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        membre = JuryActor.objects.get(uuid=self.member.uuid)
        self.assertEqual(membre.role, "PRESIDENT")

    def test_patch_other_student(self):
        self.client.force_authenticate(user=self.other_student_user)
        response = self.client.patch(self.url, data=self.updated_role_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_patch_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.patch(self.url, data=self.updated_role_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_patch_reference_promoter(self):
        self.client.force_authenticate(user=self.reference_promoter_user)
        response = self.client.patch(self.url, data=self.updated_role_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_patch_reference_promoter(self):
        self.client.force_authenticate(user=self.reference_promoter_user)
        self.parcours_doctoral.status = ChoixStatutParcoursDoctoral.JURY_SOUMIS.name
        self.parcours_doctoral.save(update_fields=["status"])
        response = self.client.patch(self.url, data=self.updated_role_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_patch_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.patch(self.url, data=self.updated_role_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_patch_committee_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.patch(self.url, data=self.updated_role_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    # DELETE
    def test_delete_no_role(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_delete_using_api_student(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)

        with self.assertRaises(JuryActor.DoesNotExist):
            JuryActor.objects.get(uuid=self.member.uuid)

    def test_delete_other_student(self):
        self.client.force_authenticate(user=self.other_student_user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_delete_promoter(self):
        self.client.force_authenticate(user=self.promoter_user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_delete_reference_promoter(self):
        self.client.force_authenticate(user=self.reference_promoter_user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)

    def test_delete_other_promoter(self):
        self.client.force_authenticate(user=self.other_promoter_user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_delete_committee_member(self):
        self.client.force_authenticate(user=self.committee_member_user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)
