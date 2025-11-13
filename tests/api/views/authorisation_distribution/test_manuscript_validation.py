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
from email import message_from_string
from email.utils import getaddresses

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
)
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.validator.exceptions import (
    MotifRefusNonSpecifieException,
    SignataireNonInviteException,
)
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.jury.domain.model.enums import FormuleDefense
from parcours_doctoral.models import ParcoursDoctoral
from parcours_doctoral.models.thesis_distribution_authorization import (
    ThesisDistributionAuthorization,
    ThesisDistributionAuthorizationActor,
)
from parcours_doctoral.tests.factories.authorization_distribution import (
    PromoterThesisDistributionAuthorizationActorFactory,
    ThesisDistributionAuthorizationFactory,
)
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.roles import (
    ScebManagerRoleFactory,
    StudentRoleFactory,
)
from reference.tests.factories.language import LanguageFactory


class ManuscriptValidationAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_with_no_role = UserFactory()
        cls.doctorate_student = StudentRoleFactory().person
        cls.sceb_manager = ScebManagerRoleFactory().person
        cls.language = LanguageFactory()

        cls.data = {
            'motif_refus': 'Reason',
            'commentaire_interne': 'Internal comment',
            'commentaire_externe': 'External comment',
        }

    def setUp(self):
        self.doctorate: ParcoursDoctoral = ParcoursDoctoralFactory(
            student=self.doctorate_student,
            status=ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_REUSSIE.name,
            defense_method=FormuleDefense.FORMULE_1.name,
        )

        lead_promoter = self.doctorate.supervision_group.actors.filter(
            parcoursdoctoralsupervisionactor__is_reference_promoter=True,
        ).first()
        self.promoter: ThesisDistributionAuthorizationActor = PromoterThesisDistributionAuthorizationActorFactory(
            person=lead_promoter.person,
        )
        self.invited_state = StateHistory.objects.create(
            actor=self.promoter,
            state=SignatureState.INVITED.name,
        )
        self.thesis_distribution_authorization: ThesisDistributionAuthorization = (
            ThesisDistributionAuthorizationFactory(
                parcours_doctoral=self.doctorate,
                signature_group=self.promoter.process,
                status=ChoixStatutAutorisationDiffusionThese.DIFFUSION_SOUMISE.name,
            )
        )

        self.base_namespace = 'parcours_doctoral_api_v1:manuscript-validation'
        self.url = resolve_url(self.base_namespace, uuid=self.doctorate.uuid)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.doctorate_student.user)

        methods_not_allowed = [
            'delete',
            'patch',
            'post',
        ]

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_access_with_no_role(self):
        self.client.force_authenticate(self.user_with_no_role)

        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_access_with_student(self):
        self.client.force_authenticate(self.doctorate_student.user)

        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_access_depending_on_some_statuses(self):
        self.client.force_authenticate(user=self.promoter.person.user)

        # First defense method
        self.doctorate.defense_method = FormuleDefense.FORMULE_1.name
        self.doctorate.status = ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE.name

        self.doctorate.save()

        # > during the private defense
        response = self.client.put(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Second defense method
        self.doctorate.defense_method = FormuleDefense.FORMULE_2.name
        self.doctorate.status = ChoixStatutParcoursDoctoral.RECEVABILITE_SOUMISE.name

        self.doctorate.save()

        # > during the admissibility
        response = self.client.put(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # > after the admissibility but the authorization is not submitted
        self.doctorate.status = ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE.name
        self.doctorate.save()

        self.thesis_distribution_authorization.status = ChoixStatutAutorisationDiffusionThese.DIFFUSION_NON_SOUMISE.name
        self.thesis_distribution_authorization.save()

        response = self.client.put(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_refuse_the_thesis_by_the_lead_promoter_with_no_reason(self):
        self.client.force_authenticate(user=self.promoter.person.user)

        data = self.data.copy()
        data['motif_refus'] = ''

        response = self.client.put(self.url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        json_response = response.json()

        errors = json_response.get('non_field_errors', [])
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]['status_code'], MotifRefusNonSpecifieException.status_code)

    def test_refuse_the_thesis_by_the_lead_promoter_with_no_invited_promoter(self):
        self.client.force_authenticate(user=self.promoter.person.user)

        self.invited_state.delete()

        response = self.client.put(self.url, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        json_response = response.json()

        errors = json_response.get('non_field_errors', [])
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]['status_code'], SignataireNonInviteException.status_code)

    def test_refuse_the_thesis_by_the_lead_promoter(self):
        self.client.force_authenticate(user=self.promoter.person.user)

        response = self.client.put(self.url, data=self.data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.doctorate.refresh_from_db()
        self.thesis_distribution_authorization.refresh_from_db()

        # Check that the data have been updated
        self.assertEqual(
            self.thesis_distribution_authorization.status,
            ChoixStatutAutorisationDiffusionThese.DIFFUSION_REFUSEE_PROMOTEUR.name,
        )

        # Check that the approval data have been saved
        group = self.thesis_distribution_authorization.signature_group
        self.assertIsNotNone(group)

        actors: QuerySet[Actor] = group.actors.all()
        self.assertEqual(len(actors), 1)

        self.assertEqual(actors[0].person, self.promoter.person)
        self.assertEqual(actors[0].thesisdistributionauthorizationactor.rejection_reason, self.data['motif_refus'])
        self.assertEqual(
            actors[0].thesisdistributionauthorizationactor.internal_comment, self.data['commentaire_interne']
        )
        self.assertEqual(actors[0].thesisdistributionauthorizationactor.role, RoleActeur.PROMOTEUR.name)
        self.assertEqual(actors[0].comment, self.data['commentaire_externe'])

        states: QuerySet[StateHistory] = actors[0].states.all()
        self.assertEqual(len(states), 2)

        self.assertEqual(states[0].state, SignatureState.DECLINED.name)

        # Check that the notification has been sent
        self.assertEqual(EmailNotification.objects.count(), 1)

        notification_to_student = EmailNotification.objects.filter(person=self.doctorate.student).first()
        self.assertIsNotNone(notification_to_student)

        email_message = message_from_string(notification_to_student.payload)
        to_email_addresses = [address for _, address in getaddresses(email_message.get_all('To', [('', '')]))]
        cc_email_addresses = [address for _, address in getaddresses(email_message.get_all('Cc', [('', '')]))]
        self.assertEqual(len(to_email_addresses), 1)
        self.assertEqual(to_email_addresses[0], self.doctorate.student.email)
        self.assertEqual(len(cc_email_addresses), 1)
        self.assertEqual(cc_email_addresses, [''])
