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
import datetime
from uuid import uuid4

import freezegun
from django.shortcuts import resolve_url
from rest_framework import status
from rest_framework.test import APITestCase

from base.models.enums.entity_type import EntityType
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from parcours_doctoral.ddd.domain.model.enums import (
    ChoixDoctoratDejaRealise,
    ChoixStatutParcoursDoctoral,
    ChoixTypeFinancement,
)
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.supervision import PromoterFactory
from parcours_doctoral.tests.mixins import CheckActionLinksMixin
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.language import LanguageFactory
from reference.tests.factories.scholarship import DoctorateScholarshipFactory


class ParcoursDoctoralAPIViewTestCase(CheckActionLinksMixin, APITestCase):
    @classmethod
    @freezegun.freeze_time('2023-01-01')
    def setUpTestData(cls):
        # Create supervision group members
        promoter = PromoterFactory()

        # Create parcours_doctoral management entity
        root = EntityVersionFactory(parent=None).entity
        cls.sector = EntityVersionFactory(
            parent=root,
            entity_type=EntityType.SECTOR.name,
            acronym='SST',
        )
        cls.commission = EntityVersionFactory(
            parent=cls.sector.entity,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        )
        cls.scholarship = DoctorateScholarshipFactory()
        cls.doctorate = ParcoursDoctoralFactory(
            training__management_entity=cls.commission.entity,
            supervision_group=promoter.process,
            training__enrollment_campus__name='Mons',
            # Cotutelle information
            cotutelle=True,
            cotutelle_motivation='abcd',
            cotutelle_institution_fwb=True,
            cotutelle_institution=cls.commission.uuid,
            cotutelle_other_institution_name='Institution A',
            cotutelle_other_institution_address='Address A',
            cotutelle_opening_request=[uuid4()],
            cotutelle_convention=[uuid4()],
            cotutelle_other_documents=[uuid4()],
            # Project information
            thesis_language=LanguageFactory(),
            thesis_institute=cls.sector,
            thesis_location='Location A',
            phd_alread_started=True,
            phd_alread_started_institute='Institute A',
            work_start_date=datetime.date(2023, 1, 1),
            phd_already_done=ChoixDoctoratDejaRealise.YES.name,
            phd_already_done_institution='Institute B',
            phd_already_done_thesis_domain='Thesis domain',
            phd_already_done_defense_date=datetime.date(2023, 1, 2),
            phd_already_done_no_defense_reason='No defense reason',
            # Funding information
            financing_type=ChoixTypeFinancement.WORK_CONTRACT.name,
            financing_work_contract='Working contract',
            financing_eft=10,
            international_scholarship=cls.scholarship,
            other_international_scholarship='Other scholarship',
            scholarship_start_date=datetime.date(2023, 1, 3),
            scholarship_end_date=datetime.date(2024, 1, 4),
            scholarship_proof=[uuid4()],
            planned_duration=20,
            dedicated_time=30,
            is_fnrs_fria_fresh_csc_linked=True,
            financing_comment='Funding comment',
        )
        cls.first_teaching_campus = (
            cls.doctorate.training.educationgroupversion_set.first().root_group.main_teaching_campus
        )
        cls.first_teaching_campus.country = CountryFactory()
        cls.first_teaching_campus.save()

        cls.other_parcours_doctoral = ParcoursDoctoralFactory(
            training__management_entity=cls.commission.entity,
        )
        # Users
        cls.student = cls.doctorate.student
        cls.other_student = cls.other_parcours_doctoral.student
        cls.no_role_user = PersonFactory().user

        cls.base_url = 'parcours_doctoral_api_v1:doctorate'

        cls.url = resolve_url(cls.base_url, uuid=cls.doctorate.uuid)

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

    def test_get_parcours_doctoral_with_other_student_is_forbidden(self):
        self.client.force_authenticate(user=self.other_student.user)
        response = self.client.get(self.url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_parcours_doctoral_with_user_not_logged_is_forbidden(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_parcours_doctoral_with_user_with_no_role_is_forbidden(self):
        self.client.force_authenticate(user=self.no_role_user)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_parcours_doctoral_of_in_creation_doctorate_is_forbidden(self):
        self.client.force_authenticate(user=self.student.user)

        in_creation_doctorate = ParcoursDoctoralFactory(
            supervision_group=self.doctorate.supervision_group,
            student=self.student,
            status=ChoixStatutParcoursDoctoral.EN_COURS_DE_CREATION_PAR_GESTIONNAIRE.name,
        )

        url = resolve_url(self.base_url, uuid=in_creation_doctorate.uuid)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        in_creation_doctorate.status = ChoixStatutParcoursDoctoral.EN_ATTENTE_INJECTION_EPC.name
        in_creation_doctorate.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @freezegun.freeze_time('2023-01-01')
    def test_get_parcours_doctoral_student(self):
        self.client.force_authenticate(user=self.student.user)
        response = self.client.get(self.url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        json_response = response.json()

        # Check parcours_doctoral links
        self.assertTrue('links' in json_response)

        self.assertActionLinks(
            links=json_response['links'],
            allowed_actions=[
                'retrieve_project',
                'retrieve_cotutelle',
                'update_cotutelle',
                'retrieve_funding',
                'update_funding',
                'retrieve_supervision',
                'retrieve_supervision_canvas',
                'retrieve_confirmation',
                'retrieve_doctorate_training',
                'retrieve_course_enrollment',
                'add_training',
                'submit_training',
                'retrieve_jury_preparation',
                'list_jury_members',
                'update_confirmation',
                'update_confirmation_extension',
            ],
            forbidden_actions=[
                'retrieve_complementary_training',
                'assent_training',
                'update_jury_preparation',
                'create_jury_members',
            ],
        )

        # Check doctorate properties

        # Global
        self.assertEqual(json_response['uuid'], str(self.doctorate.uuid))
        self.assertEqual(json_response['uuid_admission'], str(self.doctorate.admission.uuid))
        self.assertEqual(json_response['reference'], f'M-CDA22-{self.doctorate.reference_str}')
        self.assertEqual(json_response['statut'], self.doctorate.status)
        self.assertEqual(json_response['matricule_doctorant'], self.doctorate.student.global_id)
        self.assertEqual(json_response['prenom_doctorant'], self.doctorate.student.first_name)
        self.assertEqual(json_response['nom_doctorant'], self.doctorate.student.last_name)
        self.assertEqual(json_response['cree_le'], self.doctorate.created_at.isoformat())
        self.assertEqual(json_response['genre_doctorant'], self.doctorate.student.gender)
        self.assertEqual(json_response['commission_proximite'], self.doctorate.proximity_commission)
        self.assertEqual(json_response['noma_doctorant'], self.doctorate.student.student_set.first().registration_id)

        # Training
        self.assertEqual(json_response['formation']['code'], self.doctorate.training.partial_acronym)
        self.assertEqual(json_response['formation']['annee'], self.doctorate.training.academic_year.year)
        self.assertEqual(json_response['formation']['intitule'], self.doctorate.training.title)
        self.assertEqual(json_response['formation']['intitule_fr'], self.doctorate.training.title)
        self.assertEqual(json_response['formation']['intitule_en'], self.doctorate.training.title_english)
        self.assertEqual(json_response['formation']['entite_gestion']['sigle'], self.commission.acronym)
        self.assertEqual(json_response['formation']['entite_gestion']['intitule'], self.commission.title)
        self.assertEqual(json_response['formation']['entite_gestion']['lieu'], self.commission.entity.location)
        self.assertEqual(
            json_response['formation']['entite_gestion']['code_postal'],
            self.commission.entity.postal_code,
        )
        self.assertEqual(json_response['formation']['entite_gestion']['ville'], self.commission.entity.city)
        self.assertEqual(json_response['formation']['entite_gestion']['pays'], self.commission.entity.country.iso_code)
        self.assertEqual(json_response['formation']['entite_gestion']['numero_telephone'], self.commission.entity.phone)
        self.assertEqual(json_response['formation']['entite_gestion']['code_secteur'], self.sector.acronym)
        self.assertEqual(json_response['formation']['entite_gestion']['intitule_secteur'], self.sector.title)
        self.assertEqual(json_response['formation']['campus']['uuid'], str(self.first_teaching_campus.uuid))
        self.assertEqual(json_response['formation']['campus']['nom'], self.first_teaching_campus.name)
        self.assertEqual(json_response['formation']['campus']['code_postal'], self.first_teaching_campus.postal_code)
        self.assertEqual(json_response['formation']['campus']['ville'], self.first_teaching_campus.city)
        self.assertEqual(
            json_response['formation']['campus']['pays_iso_code'],
            self.first_teaching_campus.country.iso_code,
        )
        self.assertEqual(json_response['formation']['campus']['nom_pays'], self.first_teaching_campus.country.name)
        self.assertEqual(json_response['formation']['campus']['rue'], self.first_teaching_campus.street)
        self.assertEqual(json_response['formation']['campus']['numero_rue'], self.first_teaching_campus.street_number)
        self.assertEqual(json_response['formation']['campus']['boite_postale'], self.first_teaching_campus.postal_box)
        self.assertEqual(json_response['formation']['campus']['localisation'], self.first_teaching_campus.location)
        self.assertEqual(json_response['formation']['type'], self.doctorate.training.education_group_type.name)

        # Cotutelle
        self.assertEqual(json_response['cotutelle']['cotutelle'], self.doctorate.cotutelle)
        self.assertEqual(json_response['cotutelle']['motivation'], self.doctorate.cotutelle_motivation)
        self.assertEqual(json_response['cotutelle']['institution_fwb'], self.doctorate.cotutelle_institution_fwb)
        self.assertEqual(json_response['cotutelle']['institution'], str(self.doctorate.cotutelle_institution))
        self.assertEqual(json_response['cotutelle']['autre_institution'], True)
        self.assertEqual(
            json_response['cotutelle']['autre_institution_nom'], self.doctorate.cotutelle_other_institution_name
        )
        self.assertEqual(
            json_response['cotutelle']['autre_institution_adresse'], self.doctorate.cotutelle_other_institution_address
        )
        self.assertEqual(
            json_response['cotutelle']['demande_ouverture'], [str(self.doctorate.cotutelle_opening_request[0])]
        )
        self.assertEqual(json_response['cotutelle']['convention'], [str(self.doctorate.cotutelle_convention[0])])
        self.assertEqual(
            json_response['cotutelle']['autres_documents'], [str(self.doctorate.cotutelle_other_documents[0])]
        )

        # Funding
        self.assertEqual(json_response['financement']['type'], self.doctorate.financing_type)
        self.assertEqual(json_response['financement']['type_contrat_travail'], self.doctorate.financing_work_contract)
        self.assertEqual(json_response['financement']['eft'], self.doctorate.financing_eft)
        self.assertEqual(
            json_response['financement']['bourse_recherche']['uuid'], str(self.doctorate.international_scholarship.uuid)
        )
        self.assertEqual(
            json_response['financement']['bourse_recherche']['nom_court'],
            self.doctorate.international_scholarship.short_name,
        )
        self.assertEqual(
            json_response['financement']['bourse_recherche']['nom_long'],
            self.doctorate.international_scholarship.long_name,
        )
        self.assertEqual(
            json_response['financement']['autre_bourse_recherche'], self.doctorate.other_international_scholarship
        )
        self.assertEqual(
            json_response['financement']['bourse_date_debut'], self.doctorate.scholarship_start_date.isoformat()
        )
        self.assertEqual(
            json_response['financement']['bourse_date_fin'], self.doctorate.scholarship_end_date.isoformat()
        )
        self.assertEqual(json_response['financement']['bourse_preuve'], [str(self.doctorate.scholarship_proof[0])])
        self.assertEqual(json_response['financement']['duree_prevue'], self.doctorate.planned_duration)

        # Project
        self.assertEqual(json_response['projet']['titre'], self.doctorate.project_title)
        self.assertEqual(json_response['projet']['resume'], self.doctorate.project_abstract)
        self.assertEqual(json_response['projet']['documents_projet'], [str(self.doctorate.project_document[0])])
        self.assertEqual(json_response['projet']['graphe_gantt'], [str(self.doctorate.gantt_graph[0])])
        self.assertEqual(
            json_response['projet']['proposition_programme_doctoral'], [str(self.doctorate.program_proposition[0])]
        )
        self.assertEqual(
            json_response['projet']['projet_formation_complementaire'],
            [str(self.doctorate.additional_training_project[0])],
        )
        self.assertEqual(
            json_response['projet']['lettres_recommandation'], [str(self.doctorate.recommendation_letters[0])]
        )
        self.assertEqual(json_response['projet']['langue_redaction_these'], self.doctorate.thesis_language.code)
        self.assertEqual(json_response['projet']['nom_langue_redaction_these'], self.doctorate.thesis_language.name)
        self.assertEqual(json_response['projet']['institut_these'], str(self.doctorate.thesis_institute.uuid))
        self.assertEqual(json_response['projet']['nom_institut_these'], self.doctorate.thesis_institute.title)
        self.assertEqual(json_response['projet']['sigle_institut_these'], self.doctorate.thesis_institute.acronym)
        self.assertEqual(json_response['projet']['lieu_these'], self.doctorate.thesis_location)
        self.assertEqual(json_response['projet']['projet_doctoral_deja_commence'], self.doctorate.phd_alread_started)
        self.assertEqual(
            json_response['projet']['projet_doctoral_institution'], self.doctorate.phd_alread_started_institute
        )
        self.assertEqual(
            json_response['projet']['projet_doctoral_date_debut'], self.doctorate.work_start_date.isoformat()
        )
        self.assertEqual(json_response['projet']['doctorat_deja_realise'], self.doctorate.phd_already_done)
        self.assertEqual(json_response['projet']['institution'], self.doctorate.phd_already_done_institution)
        self.assertEqual(json_response['projet']['domaine_these'], self.doctorate.phd_already_done_thesis_domain)
        self.assertEqual(
            json_response['projet']['date_soutenance'], self.doctorate.phd_already_done_defense_date.isoformat()
        )
        self.assertEqual(
            json_response['projet']['raison_non_soutenue'], self.doctorate.phd_already_done_no_defense_reason
        )
