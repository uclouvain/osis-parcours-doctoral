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

import freezegun
from base.models.enums.entity_type import EntityType
from base.tests import QueriesAssertionsMixin
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from django.shortcuts import resolve_url
from reference.tests.factories.country import CountryFactory
from rest_framework import status
from rest_framework.test import APITestCase

from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.supervision import (
    CaMemberFactory,
    PromoterFactory,
)


class SupervisedDoctorateListViewTestCase(QueriesAssertionsMixin, APITestCase):
    @classmethod
    @freezegun.freeze_time('2023-01-01')
    def setUpTestData(cls):
        # Create supervision group members
        cls.promoter = PromoterFactory()
        cls.committee_member = CaMemberFactory(process=cls.promoter.process)

        cls.sector = EntityVersionFactory(
            parent=None,
            entity_type=EntityType.SECTOR.name,
            acronym='SST',
        )

        cls.commission = EntityVersionFactory(
            parent=cls.sector.entity,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        )

        cls.second_commission = EntityVersionFactory(
            parent=cls.sector.entity,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDSS',
        )

        cls.first_doctorate = ParcoursDoctoralFactory(
            training__management_entity=cls.commission.entity,
            supervision_group=cls.promoter.process,
        )

        cls.first_teaching_campus = (
            cls.first_doctorate.training.educationgroupversion_set.first().root_group.main_teaching_campus
        )
        cls.first_teaching_campus.country = CountryFactory()
        cls.first_teaching_campus.save()

        with freezegun.freeze_time('2023-01-02'):
            cls.second_doctorate = ParcoursDoctoralFactory(
                training__management_entity=cls.second_commission.entity,
                supervision_group=cls.promoter.process,
            )
            cls.second_teaching_campus = (
                cls.first_doctorate.training.educationgroupversion_set.first().root_group.main_teaching_campus
            )

        cls.other_doctorate = ParcoursDoctoralFactory(
            training__management_entity=cls.commission.entity,
        )

        # Users
        cls.student = cls.first_doctorate.student
        cls.no_role_user = PersonFactory().user

        cls.url = resolve_url('parcours_doctoral_api_v1:supervised_list')

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.student.user)
        methods_not_allowed = [
            'delete',
            'put',
            'patch',
            'post',
        ]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_list_with_user_not_logged_is_forbidden(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_with_student_is_forbidden(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_with_user_with_no_role_is_forbidden(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_with_promoter(self):
        self.client.force_authenticate(user=self.promoter.person.user)

        with self.assertNumQueriesLessThan(11, verbose=True):
            response = self.client.get(self.url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        json_response = response.json()

        self.assertEqual(len(json_response), 2)

        first_doctorate = json_response[1]
        second_doctorate = json_response[0]

        self.assertEqual(first_doctorate['uuid'], str(self.first_doctorate.uuid))
        self.assertEqual(first_doctorate['statut'], self.first_doctorate.status)
        self.assertEqual(first_doctorate['matricule_doctorant'], self.first_doctorate.student.global_id)
        self.assertEqual(first_doctorate['genre_doctorant'], self.first_doctorate.student.gender)
        self.assertEqual(first_doctorate['prenom_doctorant'], self.first_doctorate.student.first_name)
        self.assertEqual(first_doctorate['nom_doctorant'], self.first_doctorate.student.last_name)
        self.assertEqual(first_doctorate['cree_le'], self.first_doctorate.created_at.isoformat())
        self.assertEqual(first_doctorate['formation']['sigle'], self.first_doctorate.training.acronym)
        self.assertEqual(first_doctorate['formation']['code'], self.first_doctorate.training.partial_acronym)
        self.assertEqual(first_doctorate['formation']['annee'], self.first_doctorate.training.academic_year.year)
        self.assertEqual(first_doctorate['formation']['intitule'], self.first_doctorate.training.title)
        self.assertEqual(first_doctorate['formation']['intitule_fr'], self.first_doctorate.training.title)
        self.assertEqual(first_doctorate['formation']['intitule_en'], self.first_doctorate.training.title_english)
        self.assertEqual(first_doctorate['formation']['entite_gestion']['sigle'], self.commission.acronym)
        self.assertEqual(first_doctorate['formation']['entite_gestion']['intitule'], self.commission.title)
        self.assertEqual(first_doctorate['formation']['entite_gestion']['lieu'], self.commission.entity.location)
        self.assertEqual(
            first_doctorate['formation']['entite_gestion']['code_postal'], self.commission.entity.postal_code
        )
        self.assertEqual(first_doctorate['formation']['entite_gestion']['ville'], self.commission.entity.city)
        self.assertEqual(
            first_doctorate['formation']['entite_gestion']['pays'], self.commission.entity.country.iso_code
        )
        self.assertEqual(
            first_doctorate['formation']['entite_gestion']['numero_telephone'], self.commission.entity.phone
        )
        self.assertEqual(first_doctorate['formation']['entite_gestion']['code_secteur'], self.sector.acronym)
        self.assertEqual(first_doctorate['formation']['entite_gestion']['intitule_secteur'], self.sector.title)
        self.assertEqual(first_doctorate['formation']['campus']['uuid'], str(self.first_teaching_campus.uuid))
        self.assertEqual(first_doctorate['formation']['campus']['nom'], self.first_teaching_campus.name)
        self.assertEqual(first_doctorate['formation']['campus']['code_postal'], self.first_teaching_campus.postal_code)
        self.assertEqual(first_doctorate['formation']['campus']['ville'], self.first_teaching_campus.city)
        self.assertEqual(
            first_doctorate['formation']['campus']['pays_iso_code'],
            self.first_teaching_campus.country.iso_code,
        )
        self.assertEqual(first_doctorate['formation']['campus']['nom_pays'], self.first_teaching_campus.country.name)
        self.assertEqual(first_doctorate['formation']['campus']['rue'], self.first_teaching_campus.street)
        self.assertEqual(first_doctorate['formation']['campus']['numero_rue'], self.first_teaching_campus.street_number)
        self.assertEqual(first_doctorate['formation']['campus']['boite_postale'], self.first_teaching_campus.postal_box)
        self.assertEqual(first_doctorate['formation']['campus']['localisation'], self.first_teaching_campus.location)
        self.assertEqual(first_doctorate['formation']['type'], self.first_doctorate.training.education_group_type.name)

        self.assertEqual(second_doctorate['uuid'], str(self.second_doctorate.uuid))

    def test_list_with_ca_member(self):
        self.client.force_authenticate(user=self.committee_member.person.user)

        with self.assertNumQueriesLessThan(11, verbose=True):
            response = self.client.get(self.url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        json_response = response.json()

        self.assertEqual(len(json_response), 2)

        first_doctorate = json_response[1]
        second_doctorate = json_response[0]

        self.assertEqual(first_doctorate['uuid'], str(self.first_doctorate.uuid))
        self.assertEqual(second_doctorate['uuid'], str(self.second_doctorate.uuid))
