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

from django.db.models import QuerySet
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.translation import gettext
from osis_notification.models import EmailNotification
from osis_signature.enums import SignatureState
from osis_signature.models import Actor, StateHistory
from rest_framework import status

from admission.tests.factories.doctorate import DoctorateFactory
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from parcours_doctoral.ddd.autorisation_diffusion_these.domain.model.enums import (
    ChoixEtatSignature,
    ChoixStatutAutorisationDiffusionThese,
    RoleActeur,
    TypeModalitesDiffusionThese,
)
from parcours_doctoral.ddd.autorisation_diffusion_these.dtos.autorisation_diffusion_these import (
    AutorisationDiffusionTheseDTO,
)
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.domain.model.parcours_doctoral import ENTITY_CDE
from parcours_doctoral.ddd.jury.domain.model.enums import FormuleDefense, RoleJury
from parcours_doctoral.forms.manuscript_validation import (
    ManuscriptValidationApprovalForm,
)
from parcours_doctoral.models import ParcoursDoctoral
from parcours_doctoral.models.thesis_distribution_authorization import (
    ThesisDistributionAuthorization,
    ThesisDistributionAuthorizationActor,
)
from parcours_doctoral.tests.factories.authorization_distribution import (
    AdreThesisDistributionAuthorizationActorFactory,
    PromoterThesisDistributionAuthorizationActorFactory,
    ThesisDistributionAuthorizationFactory,
)
from parcours_doctoral.tests.factories.jury import JuryActorFactory
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.roles import (
    AdreManagerRoleFactory,
    ScebManagerRoleFactory,
)
from parcours_doctoral.tests.mixins import MockOsisDocumentMixin


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class ManuscriptValidationFormViewWithAdreManagerTestCase(MockOsisDocumentMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        cls.doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=cls.doctoral_commission, acronym=ENTITY_CDE)

        cls.training = DoctorateFactory()

        cls.student = PersonFactory()
        cls.manager = ProgramManagerFactory(education_group=cls.training.education_group).person
        cls.adre_manager_role = AdreManagerRoleFactory()
        cls.sceb_manager = ScebManagerRoleFactory().person

        cls.reject_data = {
            'decision': ChoixEtatSignature.DECLINED.name,
            'motif_refus': 'Reason',
            'commentaire_interne': 'Internal comment 0',
            'commentaire_externe': 'External comment 0',
        }
        cls.accept_data = {
            'decision': ChoixEtatSignature.APPROVED.name,
            'commentaire_interne': 'Internal comment 1',
            'commentaire_externe': 'External comment 1',
        }

        cls.namespace = 'parcours_doctoral:update:manuscript-validation'
        cls.detail_namespace = 'parcours_doctoral:manuscript-validation'

    def setUp(self):
        super().setUp()

        self.doctorate: ParcoursDoctoral = ParcoursDoctoralFactory(
            student=self.student,
            status=ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_REUSSIE.name,
            defense_method=FormuleDefense.FORMULE_1.name,
        )

        # Promoter
        jury_promoter = self.doctorate.jury_group.actors.filter(juryactor__is_lead_promoter=True).first()
        jury_promoter.save()
        self.promoter: ThesisDistributionAuthorizationActor = PromoterThesisDistributionAuthorizationActorFactory(
            person=jury_promoter.person,
        )

        # Adre
        self.jury_adre = JuryActorFactory(
            process=self.doctorate.jury_group,
            role=RoleJury.ADRE.name,
            person=self.adre_manager_role.person,
        )
        self.adre_manager: ThesisDistributionAuthorizationActor = AdreThesisDistributionAuthorizationActorFactory(
            person=self.jury_adre.person,
            process=self.promoter.process,
        )
        self.adre_manager_invited_state = StateHistory.objects.create(
            actor=self.adre_manager,
            state=SignatureState.INVITED.name,
        )

        self.thesis_distribution_authorization: ThesisDistributionAuthorization = (
            ThesisDistributionAuthorizationFactory(
                parcours_doctoral=self.doctorate,
                status=ChoixStatutAutorisationDiffusionThese.DIFFUSION_VALIDEE_PROMOTEUR.name,
                funding_sources='Funding sources',
                thesis_summary_in_english='Summary in english',
                thesis_summary_in_other_language='Summary in other language',
                thesis_keywords=['word1', 'word2'],
                conditions=TypeModalitesDiffusionThese.ACCES_EMBARGO.name,
                embargo_date=datetime.date(2025, 1, 15),
                additional_limitation_for_specific_chapters='Additional limitation',
                accepted_on=datetime.date(2026, 2, 3),
                acceptation_content='Accepted content',
                signature_group=self.adre_manager.process,
            )
        )

        self.url = resolve_url(self.namespace, uuid=self.doctorate.uuid)
        self.details_url = resolve_url(self.detail_namespace, uuid=self.doctorate.uuid)

    def test_access_depending_on_some_statuses(self):
        self.client.force_login(user=self.adre_manager_role.person.user)

        # First defense method
        self.doctorate.defense_method = FormuleDefense.FORMULE_1.name
        self.doctorate.status = ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE.name

        self.doctorate.save()

        # > during the private defense
        response = self.client.post(self.url, data=self.reject_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Second defense method
        self.doctorate.defense_method = FormuleDefense.FORMULE_2.name
        self.doctorate.status = ChoixStatutParcoursDoctoral.RECEVABILITE_SOUMISE.name

        self.doctorate.save()

        # > during the admissibility
        response = self.client.post(self.url, data=self.reject_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # > after the admissibility but the authorization is not validated by the promoter
        self.doctorate.status = ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE.name
        self.doctorate.save()

        self.thesis_distribution_authorization.status = ChoixStatutAutorisationDiffusionThese.DIFFUSION_SOUMISE.name
        self.thesis_distribution_authorization.save()

        response = self.client.post(self.url, data=self.reject_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_with_valid_access(self):
        self.client.force_login(self.adre_manager_role.person.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        authorization_distribution: AutorisationDiffusionTheseDTO = response.context.get('authorization_distribution')

        self.thesis_distribution_authorization.refresh_from_db()

        self.assertEqual(
            authorization_distribution.statut,
            ChoixStatutAutorisationDiffusionThese.DIFFUSION_VALIDEE_PROMOTEUR.name,
        )

        signatories = response.context.get('signatories')

        self.assertEqual(len(signatories), 2)

        adre_manager_dto = signatories.get(RoleActeur.ADRE.name)

        self.assertIsNotNone(adre_manager_dto)
        self.assertEqual(adre_manager_dto.uuid, str(self.adre_manager.uuid))
        self.assertEqual(adre_manager_dto.signature.etat, self.adre_manager_invited_state.state)

        self.assertIn(adre_manager_dto, authorization_distribution.signataires)

        form = response.context.get('form')
        self.assertIsInstance(form, ManuscriptValidationApprovalForm)

    def test_refuse_the_thesis_with_missing_data(self):
        self.client.force_login(user=self.adre_manager_role.person.user)

        # The decision is missing
        data = self.reject_data.copy()
        data['decision'] = ''

        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context.get('form')

        self.assertFalse(form.is_valid())

        self.assertIn(
            FIELD_REQUIRED_MESSAGE,
            form.errors.get('decision', []),
        )

        # The refusal reason is missing
        data = self.reject_data.copy()
        data['motif_refus'] = ''

        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context.get('form')

        self.assertFalse(form.is_valid())

        self.assertIn(
            FIELD_REQUIRED_MESSAGE,
            form.errors.get('motif_refus', []),
        )

    def test_refuse_the_thesis_with_no_invited_adre_manager(self):
        self.client.force_login(user=self.adre_manager_role.person.user)

        self.adre_manager_invited_state.delete()

        response = self.client.post(self.url, data=self.reject_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context.get('form')

        self.assertFalse(form.is_valid())

        self.assertIn(
            gettext('You must be invited to do this action.'),
            form.errors.get('__all__', []),
        )

    def test_refuse_the_thesis(self):
        self.client.force_login(user=self.adre_manager_role.person.user)

        response = self.client.post(self.url, data=self.reject_data)

        self.assertRedirects(response, self.details_url)

        self.doctorate.refresh_from_db()
        self.thesis_distribution_authorization.refresh_from_db()

        # Check that the data have been updated
        self.assertEqual(
            self.thesis_distribution_authorization.status,
            ChoixStatutAutorisationDiffusionThese.DIFFUSION_REFUSEE_ADRE.name,
        )

        # Check that the approval data have been saved
        group = self.thesis_distribution_authorization.signature_group
        self.assertIsNotNone(group)

        adre_managers: QuerySet[Actor] = group.actors.filter(
            thesisdistributionauthorizationactor__role=RoleActeur.ADRE.name,
        )
        self.assertEqual(len(adre_managers), 1)

        self.assertEqual(adre_managers[0].person, self.adre_manager.person)
        self.assertEqual(
            adre_managers[0].thesisdistributionauthorizationactor.rejection_reason,
            self.reject_data['motif_refus'],
        )
        self.assertEqual(
            adre_managers[0].thesisdistributionauthorizationactor.internal_comment,
            self.reject_data['commentaire_interne'],
        )
        self.assertEqual(adre_managers[0].thesisdistributionauthorizationactor.role, RoleActeur.ADRE.name)
        self.assertEqual(adre_managers[0].comment, self.reject_data['commentaire_externe'])

        states: QuerySet[StateHistory] = adre_managers[0].states.all()
        self.assertEqual(len(states), 2)

        self.assertEqual(states[1].state, SignatureState.DECLINED.name)

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
        self.assertEqual(cc_email_addresses[0], self.promoter.person.email)

    def test_accept_the_thesis_with_no_invited_adre_manager(self):
        self.client.force_login(user=self.adre_manager_role.person.user)

        self.adre_manager_invited_state.delete()

        response = self.client.post(self.url, data=self.accept_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        form = response.context.get('form')

        self.assertFalse(form.is_valid())

        self.assertIn(
            gettext('You must be invited to do this action.'),
            form.errors.get('__all__', []),
        )

    def test_accept_the_thesis(self):
        self.client.force_login(user=self.adre_manager_role.person.user)

        response = self.client.post(self.url, data=self.accept_data)

        self.assertRedirects(response, self.details_url)

        self.doctorate.refresh_from_db()
        self.thesis_distribution_authorization.refresh_from_db()

        # Check that the data have been updated
        self.assertEqual(
            self.thesis_distribution_authorization.status,
            ChoixStatutAutorisationDiffusionThese.DIFFUSION_VALIDEE_ADRE.name,
        )

        # Check that the approval data have been saved
        group = self.thesis_distribution_authorization.signature_group
        self.assertIsNotNone(group)

        adre_managers: QuerySet[Actor] = group.actors.filter(
            thesisdistributionauthorizationactor__role=RoleActeur.ADRE.name,
        )
        self.assertEqual(len(adre_managers), 1)

        self.assertEqual(adre_managers[0].person, self.adre_manager.person)
        self.assertEqual(adre_managers[0].thesisdistributionauthorizationactor.rejection_reason, '')
        self.assertEqual(
            adre_managers[0].thesisdistributionauthorizationactor.internal_comment,
            self.accept_data['commentaire_interne'],
        )
        self.assertEqual(adre_managers[0].thesisdistributionauthorizationactor.role, RoleActeur.ADRE.name)
        self.assertEqual(adre_managers[0].comment, self.accept_data['commentaire_externe'])

        states: QuerySet[StateHistory] = adre_managers[0].states.all()
        self.assertEqual(len(states), 2)

        self.assertEqual(states[1].state, SignatureState.APPROVED.name)

        # Check that the sceb manager has been invited
        sceb_managers: QuerySet[Actor] = group.actors.filter(
            thesisdistributionauthorizationactor__role=RoleActeur.SCEB.name,
        )
        self.assertEqual(len(sceb_managers), 1)

        self.assertEqual(sceb_managers[0].person, self.sceb_manager)

        states: QuerySet[StateHistory] = sceb_managers[0].states.all()
        self.assertEqual(len(states), 1)

        self.assertEqual(states[0].state, SignatureState.INVITED.name)

        # Check that the notification has been sent
        self.assertEqual(EmailNotification.objects.count(), 1)

        notification_to_student = EmailNotification.objects.filter(person=self.sceb_manager).first()
        self.assertIsNotNone(notification_to_student)

        email_message = message_from_string(notification_to_student.payload)
        to_email_addresses = [address for _, address in getaddresses(email_message.get_all('To', [('', '')]))]
        cc_email_addresses = [address for _, address in getaddresses(email_message.get_all('Cc', [('', '')]))]
        self.assertEqual(len(to_email_addresses), 1)
        self.assertEqual(to_email_addresses[0], self.sceb_manager.email)
        self.assertEqual(len(cc_email_addresses), 1)
        self.assertEqual(cc_email_addresses[0], '')
