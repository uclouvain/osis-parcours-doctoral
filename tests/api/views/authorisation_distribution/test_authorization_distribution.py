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
from email import message_from_string
from email.utils import getaddresses

import freezegun
from django.db.models import QuerySet
from django.shortcuts import resolve_url
from osis_notification.models import EmailNotification
from osis_signature.enums import SignatureState
from osis_signature.models import Actor, StateHistory
from rest_framework import status
from rest_framework.test import APITestCase

from base.tests.factories.user import UserFactory
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.enums import (
    ChoixStatutAutorisationDiffusionThese,
    RoleActeur,
    TypeModalitesDiffusionThese,
)
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.jury.domain.model.enums import FormuleDefense
from parcours_doctoral.models import JuryActor, ParcoursDoctoral
from parcours_doctoral.models.thesis_distribution_authorization import (
    ThesisDistributionAuthorizationActor,
)
from parcours_doctoral.tests.factories.authorization_distribution import (
    PromoterThesisDistributionAuthorizationActorFactory,
)
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.roles import (
    ScebManagerRoleFactory,
    StudentRoleFactory,
)
from reference.tests.factories.language import LanguageFactory


class AuthorizationDistributionAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_with_no_role = UserFactory()
        cls.doctorate_student = StudentRoleFactory().person
        cls.other_doctorate_student = StudentRoleFactory().person
        cls.sceb_manager = ScebManagerRoleFactory().person
        cls.language = LanguageFactory()

        cls.data = {
            'sources_financement': 'New funding sources',
            'resume_anglais': 'New summary in english',
            'resume_autre_langue': 'New summary in other language',
            'langue_redaction_these': cls.language.code,
            'mots_cles': ['word3', 'word4'],
            'type_modalites_diffusion': TypeModalitesDiffusionThese.ACCES_LIBRE.name,
            'date_embargo': '2025-01-16',
            'limitations_additionnelles_chapitres': 'New limitation',
            'modalites_diffusion_acceptees': 'Accepted conditions',
        }

    def setUp(self):
        self.doctorate: ParcoursDoctoral = ParcoursDoctoralFactory(
            student=self.doctorate_student,
            thesis_distribution_authorization_status=ChoixStatutAutorisationDiffusionThese.DIFFUSION_NON_SOUMISE.name,
            funding_sources='Funding sources',
            thesis_summary_in_english='Summary in english',
            thesis_summary_in_other_language='Summary in other language',
            thesis_keywords=['word1', 'word2'],
            thesis_distribution_conditions=TypeModalitesDiffusionThese.ACCES_EMBARGO.name,
            thesis_distribution_embargo_date=datetime.date(2025, 1, 15),
            thesis_distribution_additional_limitation_for_specific_chapters='Additional limitation',
            thesis_distribution_accepted_on=datetime.date(2026, 2, 3),
            thesis_distribution_acceptation_content='Accepted content',
            defense_method=FormuleDefense.FORMULE_1.name,
            status=ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_REUSSIE.name,
        )

        self.base_namespace = 'parcours_doctoral_api_v1:authorization-distribution'
        self.url = resolve_url(self.base_namespace, uuid=self.doctorate.uuid)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        methods_not_allowed = [
            'delete',
            'patch',
        ]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_access_with_no_role(self):
        self.client.force_authenticate(self.user_with_no_role)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_access_other_student(self):
        self.client.force_authenticate(self.other_doctorate_student.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_authorization_distribution_data(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        # No signature process
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()

        self.assertEqual(json_response.get('statut'), ChoixStatutAutorisationDiffusionThese.DIFFUSION_NON_SOUMISE.name)
        self.assertEqual(json_response.get('sources_financement'), 'Funding sources')
        self.assertEqual(json_response.get('resume_anglais'), 'Summary in english')
        self.assertEqual(json_response.get('resume_autre_langue'), 'Summary in other language')
        self.assertEqual(json_response.get('mots_cles'), ['word1', 'word2'])
        self.assertEqual(json_response.get('type_modalites_diffusion'), TypeModalitesDiffusionThese.ACCES_EMBARGO.name)
        self.assertEqual(json_response.get('date_embargo'), '2025-01-15')
        self.assertEqual(json_response.get('limitations_additionnelles_chapitres'), 'Additional limitation')
        self.assertEqual(json_response.get('modalites_diffusion_acceptees_le'), '2026-02-03')
        self.assertEqual(json_response.get('signataires'), [])

        # With signature process
        promoter = PromoterThesisDistributionAuthorizationActorFactory(
            comment='Comment',
            internal_comment='Internal comment',
            rejection_reason='Rejection reason',
        )

        with freezegun.freeze_time('2025-02-03'):
            promoter.switch_state(SignatureState.APPROVED)

        promoter = ThesisDistributionAuthorizationActor.objects.get(uuid=promoter.uuid)

        self.doctorate.thesis_distribution_authorization_group = promoter.process
        self.doctorate.save()

        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json_response = response.json()

        self.assertEqual(
            json_response.get('signataires'),
            [
                {
                    'uuid': str(promoter.uuid),
                    'matricule': promoter.person.global_id,
                    'nom': promoter.person.last_name,
                    'prenom': promoter.person.first_name,
                    'genre': promoter.person.gender,
                    'institution': 'UCLouvain',
                    'email': promoter.person.email,
                    'role': RoleActeur.PROMOTEUR.name,
                    'signature': {
                        'etat': SignatureState.APPROVED.name,
                        'date_heure': promoter.last_state_date.isoformat(),
                        'commentaire_externe': 'Comment',
                        'commentaire_interne': 'Internal comment',
                        'motif_refus': 'Rejection reason',
                    },
                }
            ],
        )

    def test_put_is_only_available_in_some_statuses(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        # First defense method
        self.doctorate.defense_method = FormuleDefense.FORMULE_1.name
        self.doctorate.status = ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE.name

        self.doctorate.save()

        # > during the private defense
        response = self.client.put(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # > after the private defense
        self.doctorate.status = ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_REUSSIE.name
        self.doctorate.save()

        response = self.client.put(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Second defense method
        self.doctorate.defense_method = FormuleDefense.FORMULE_2.name
        self.doctorate.status = ChoixStatutParcoursDoctoral.RECEVABILITE_SOUMISE.name

        self.doctorate.save()

        # > during the admissibility
        response = self.client.put(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # > after the admissibility
        self.doctorate.status = ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE.name
        self.doctorate.save()

        response = self.client.put(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_is_only_available_in_some_statuses(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        # First defense method
        self.doctorate.defense_method = FormuleDefense.FORMULE_1.name
        self.doctorate.status = ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE.name

        self.doctorate.save()

        # > during the private defense
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # > after the private defense
        self.doctorate.status = ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_REUSSIE.name
        self.doctorate.save()

        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Second defense method
        self.doctorate.defense_method = FormuleDefense.FORMULE_2.name
        self.doctorate.status = ChoixStatutParcoursDoctoral.RECEVABILITE_SOUMISE.name

        self.doctorate.save()

        # > during the admissibility
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # > after the admissibility
        self.doctorate.status = ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE.name
        self.doctorate.save()

        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @freezegun.freeze_time('2025-01-02')
    def test_put_new_authorization_distribution_data(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        response = self.client.put(self.url, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.doctorate.refresh_from_db()

        self.assertEqual(self.doctorate.funding_sources, self.data['sources_financement'])
        self.assertEqual(self.doctorate.thesis_summary_in_english, self.data['resume_anglais'])
        self.assertEqual(self.doctorate.thesis_summary_in_other_language, self.data['resume_autre_langue'])
        self.assertEqual(self.doctorate.thesis_language, self.language)
        self.assertEqual(self.doctorate.thesis_keywords, self.data['mots_cles'])
        self.assertEqual(self.doctorate.thesis_distribution_conditions, self.data['type_modalites_diffusion'])
        self.assertEqual(self.doctorate.thesis_distribution_embargo_date, datetime.date(2025, 1, 16))
        self.assertEqual(
            self.doctorate.thesis_distribution_additional_limitation_for_specific_chapters,
            self.data['limitations_additionnelles_chapitres'],
        )
        self.assertEqual(
            self.doctorate.thesis_distribution_acceptation_content,
            self.data['modalites_diffusion_acceptees'],
        )
        self.assertEqual(self.doctorate.thesis_distribution_accepted_on, datetime.date(2025, 1, 2))

    @freezegun.freeze_time('2025-01-02')
    def test_post_new_authorization_distribution_data(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        response = self.client.post(self.url, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.doctorate.refresh_from_db()

        # Check that the data have been updated
        self.assertEqual(self.doctorate.funding_sources, self.data['sources_financement'])
        self.assertEqual(self.doctorate.thesis_summary_in_english, self.data['resume_anglais'])
        self.assertEqual(self.doctorate.thesis_summary_in_other_language, self.data['resume_autre_langue'])
        self.assertEqual(self.doctorate.thesis_language, self.language)
        self.assertEqual(self.doctorate.thesis_keywords, self.data['mots_cles'])
        self.assertEqual(self.doctorate.thesis_distribution_conditions, self.data['type_modalites_diffusion'])
        self.assertEqual(self.doctorate.thesis_distribution_embargo_date, datetime.date(2025, 1, 16))
        self.assertEqual(
            self.doctorate.thesis_distribution_additional_limitation_for_specific_chapters,
            self.data['limitations_additionnelles_chapitres'],
        )
        self.assertEqual(
            self.doctorate.thesis_distribution_acceptation_content,
            self.data['modalites_diffusion_acceptees'],
        )
        self.assertEqual(self.doctorate.thesis_distribution_accepted_on, datetime.date(2025, 1, 2))

        self.assertEqual(
            self.doctorate.thesis_distribution_authorization_status,
            ChoixStatutAutorisationDiffusionThese.DIFFUSION_SOUMISE.name,
        )

        contact_jury_promoter = JuryActor.objects.filter(
            process__doctorate_from_jury_group=self.doctorate,
            is_lead_promoter=True,
        ).first()

        self.assertIsNotNone(contact_jury_promoter)

        # Check that the contact supervisor is invited
        group = self.doctorate.thesis_distribution_authorization_group
        self.assertIsNotNone(group)

        actors: QuerySet[Actor] = group.actors.all()
        self.assertEqual(len(actors), 1)

        self.assertEqual(actors[0].person, contact_jury_promoter.person)
        self.assertEqual(actors[0].thesisdistributionauthorizationactor.rejection_reason, '')
        self.assertEqual(actors[0].thesisdistributionauthorizationactor.internal_comment, '')
        self.assertEqual(actors[0].thesisdistributionauthorizationactor.role, RoleActeur.PROMOTEUR.name)
        self.assertEqual(actors[0].comment, '')

        states: QuerySet[StateHistory] = actors[0].states.all()
        self.assertEqual(len(states), 1)

        self.assertEqual(states[0].state, SignatureState.INVITED.name)

        # Check that notifications have been sent
        self.assertEqual(EmailNotification.objects.count(), 2)

        notification_to_supervisor = EmailNotification.objects.filter(person=actors[0].person).first()
        self.assertIsNotNone(notification_to_supervisor)

        email_message = message_from_string(notification_to_supervisor.payload)
        to_email_addresses = [address for _, address in getaddresses(email_message.get_all('To', [('', '')]))]
        self.assertEqual(len(to_email_addresses), 1)
        self.assertEqual(to_email_addresses[0], actors[0].email)

        notification_to_student = EmailNotification.objects.filter(person=self.doctorate.student).first()
        self.assertIsNotNone(notification_to_student)

        email_message = message_from_string(notification_to_student.payload)
        to_email_addresses = [address for _, address in getaddresses(email_message.get_all('To', [('', '')]))]
        cc_email_addresses = [address for _, address in getaddresses(email_message.get_all('Cc', [('', '')]))]
        self.assertEqual(to_email_addresses[0], self.doctorate.student.email)
        self.assertEqual(len(to_email_addresses), 1)
        self.assertEqual(cc_email_addresses[0], self.sceb_manager.email)
        self.assertEqual(len(cc_email_addresses), 1)
