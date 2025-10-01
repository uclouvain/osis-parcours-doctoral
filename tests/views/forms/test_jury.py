# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime
import uuid

from django.shortcuts import resolve_url
from django.test import TestCase
from django.urls import reverse
from osis_signature.enums import SignatureState
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from base.models.enums.mandate_type import MandateTypes
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.mandatary import MandataryFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.jury.domain.model.enums import (
    DecisionApprovalEnum,
    FormuleDefense,
)
from parcours_doctoral.models import JuryActor
from parcours_doctoral.models.parcours_doctoral import ParcoursDoctoral
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory
from parcours_doctoral.tests.factories.roles import (
    AdreManagerRoleFactory,
    AuditorFactory,
)
from parcours_doctoral.tests.factories.supervision import PromoterFactory
from reference.tests.factories.language import FrenchLanguageFactory, LanguageFactory


class JuryPreparationFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        promoter = PromoterFactory()
        cls.promoter = promoter.person

        # Create parcours_doctorals
        cls.parcours_doctoral = ParcoursDoctoralFactory(
            status=ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE.name,
            training__academic_year=academic_years[0],
        )

        # User with one cdd
        cls.manager = ProgramManagerFactory(education_group=cls.parcours_doctoral.training.education_group).person.user
        cls.update_path = 'parcours_doctoral:update:jury-preparation'
        cls.read_path = 'parcours_doctoral:jury-preparation'

    def setUp(self):
        self.client.force_login(user=self.manager)

    def test_get_jury_preparation_detail_cdd_user_with_unknown_parcours_doctoral(self):
        url = reverse(self.update_path, args=[uuid.uuid4()])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_get_jury_preparation_detail_cdd_user(self):
        url = reverse(self.update_path, args=[self.parcours_doctoral.uuid])

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_200_OK)

        self.assertEqual(
            response.context.get('parcours_doctoral').uuid,
            str(self.parcours_doctoral.uuid),
        )
        self.assertEqual(
            response.context['form'].initial,
            {
                'titre_propose': self.parcours_doctoral.thesis_proposed_title,
                'formule_defense': self.parcours_doctoral.defense_method,
                'date_indicative': self.parcours_doctoral.defense_indicative_date,
                'langue_redaction': (
                    self.parcours_doctoral.thesis_language if self.parcours_doctoral.thesis_language else ''
                ),
                'langue_soutenance': (
                    self.parcours_doctoral.defense_language if self.parcours_doctoral.defense_language else ''
                ),
                'commentaire': self.parcours_doctoral.comment_about_jury,
            },
        )

    def test_post_jury_preparation_detail_cdd_user(self):
        url = reverse(self.update_path, args=[self.parcours_doctoral.uuid])
        language = FrenchLanguageFactory()

        response = self.client.post(
            url,
            data={
                'titre_propose': 'Nouveau titre',
                'formule_defense': FormuleDefense.FORMULE_2.name,
                'date_indicative': '01/01/2023',
                'langue_redaction': language.code,
                'langue_soutenance': language.code,
                'commentaire': 'Nouveau commentaire',
            },
        )

        self.assertRedirects(response, resolve_url(self.read_path, uuid=self.parcours_doctoral.uuid))

        updated_parcours_doctoral = ParcoursDoctoral.objects.get(
            uuid=self.parcours_doctoral.uuid,
        )
        self.assertEqual(updated_parcours_doctoral.thesis_proposed_title, 'Nouveau titre')
        self.assertEqual(updated_parcours_doctoral.defense_method, FormuleDefense.FORMULE_2.name)
        self.assertEqual(updated_parcours_doctoral.defense_indicative_date, '01/01/2023')
        self.assertEqual(updated_parcours_doctoral.thesis_language, language)
        self.assertEqual(updated_parcours_doctoral.defense_language, language)
        self.assertEqual(updated_parcours_doctoral.comment_about_jury, 'Nouveau commentaire')


class JuryFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        MandataryFactory(
            mandate__function=MandateTypes.RECTOR.name,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(days=1),
        )

        promoter = PromoterFactory()
        cls.promoter = promoter.person

        # Create parcours_doctorals
        cls.parcours_doctoral = ParcoursDoctoralFactory(
            status=ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE.name,
            thesis_proposed_title='title',
            defense_method=FormuleDefense.FORMULE_2,
            defense_language=LanguageFactory(),
            thesis_language=LanguageFactory(),
            training__academic_year=academic_years[0],
        )

        # User with one cdd
        cls.manager = ProgramManagerFactory(education_group=cls.parcours_doctoral.training.education_group).person.user

        cls.adre_manager = AdreManagerRoleFactory()

        cls.read_path = 'parcours_doctoral:jury'

    def setUp(self):
        self.client.force_login(user=self.manager)

    def test_post_jury_request_signatures_cdd_user(self):
        url = reverse('parcours_doctoral:update:jury-request-signatures', args=[self.parcours_doctoral.uuid])

        AuditorFactory(entity=self.parcours_doctoral.thesis_institute.entity)

        response = self.client.post(url, data={})

        self.assertRedirects(response, resolve_url(self.read_path, uuid=self.parcours_doctoral.uuid))
        self.parcours_doctoral.refresh_from_db()
        self.assertEqual(self.parcours_doctoral.status, ChoixStatutParcoursDoctoral.JURY_SOUMIS.name)
        self.assertTrue(
            all(
                actor.state == SignatureState.INVITED.name
                for actor in JuryActor.objects.filter(process=self.parcours_doctoral.jury_group)
            )
        )

    def test_post_jury_reset_signatures_cdd_user(self):
        url = reverse('parcours_doctoral:update:jury-reset-signatures', args=[self.parcours_doctoral.uuid])

        for actor in JuryActor.objects.filter(process=self.parcours_doctoral.jury_group):
            actor.switch_state(SignatureState.INVITED)
        self.parcours_doctoral.status = ChoixStatutParcoursDoctoral.JURY_SOUMIS.name
        self.parcours_doctoral.save(update_fields=['status'])

        response = self.client.post(url, data={})

        self.assertRedirects(response, resolve_url(self.read_path, uuid=self.parcours_doctoral.uuid))
        self.parcours_doctoral.refresh_from_db()
        self.assertEqual(self.parcours_doctoral.status, ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE.name)
        self.assertTrue(
            all(
                actor.state == SignatureState.NOT_INVITED.name
                for actor in JuryActor.objects.filter(process=self.parcours_doctoral.jury_group)
            )
        )

    def test_post_jury_cdd_approbation_cdd_user(self):
        url = reverse('parcours_doctoral:update:jury-cdd-decision', args=[self.parcours_doctoral.uuid])

        for actor in JuryActor.objects.filter(process=self.parcours_doctoral.jury_group):
            actor.switch_state(SignatureState.APPROVED)
        self.parcours_doctoral.status = ChoixStatutParcoursDoctoral.JURY_APPROUVE_CA.name
        self.parcours_doctoral.save(update_fields=['status'])

        response = self.client.post(
            url,
            data={
                'decision': DecisionApprovalEnum.APPROVED.name,
                'commentaire_interne': 'foo',
                'commentaire_externe': 'bar',
            },
        )

        self.assertRedirects(response, resolve_url(self.read_path, uuid=self.parcours_doctoral.uuid))
        self.parcours_doctoral.refresh_from_db()
        self.assertEqual(self.parcours_doctoral.status, ChoixStatutParcoursDoctoral.JURY_APPROUVE_CDD.name)
        actor = JuryActor.objects.get(process=self.parcours_doctoral.jury_group, person=self.manager.person)
        self.assertEqual(actor.state, SignatureState.APPROVED.name)
        self.assertEqual(actor.internal_comment, 'foo')
        self.assertEqual(actor.comment, 'bar')

    def test_post_jury_cdd_refus_cdd_user(self):
        url = reverse('parcours_doctoral:update:jury-cdd-decision', args=[self.parcours_doctoral.uuid])

        for actor in JuryActor.objects.filter(process=self.parcours_doctoral.jury_group):
            actor.switch_state(SignatureState.APPROVED)
        self.parcours_doctoral.status = ChoixStatutParcoursDoctoral.JURY_APPROUVE_CA.name
        self.parcours_doctoral.save(update_fields=['status'])

        response = self.client.post(
            url,
            data={
                'decision': DecisionApprovalEnum.DECLINED.name,
                'motif_refus': 'motif',
                'commentaire_interne': 'foo',
                'commentaire_externe': 'bar',
            },
        )

        self.assertRedirects(response, resolve_url(self.read_path, uuid=self.parcours_doctoral.uuid))
        self.parcours_doctoral.refresh_from_db()
        self.assertEqual(self.parcours_doctoral.status, ChoixStatutParcoursDoctoral.JURY_REFUSE_CDD.name)
        actor = JuryActor.objects.get(process=self.parcours_doctoral.jury_group, person=self.manager.person)
        self.assertEqual(actor.state, SignatureState.DECLINED.name)
        self.assertEqual(actor.rejection_reason, 'motif')
        self.assertEqual(actor.internal_comment, 'foo')
        self.assertEqual(actor.comment, 'bar')

    def test_post_jury_adre_approbation_cdd_user(self):
        url = reverse('parcours_doctoral:update:jury-adre-decision', args=[self.parcours_doctoral.uuid])

        self.client.force_login(user=self.adre_manager.person.user)

        for actor in JuryActor.objects.filter(process=self.parcours_doctoral.jury_group):
            actor.switch_state(SignatureState.APPROVED)
        self.parcours_doctoral.status = ChoixStatutParcoursDoctoral.JURY_APPROUVE_CDD.name
        self.parcours_doctoral.save(update_fields=['status'])

        response = self.client.post(
            url,
            data={
                'decision': DecisionApprovalEnum.APPROVED.name,
                'commentaire_interne': 'foo',
                'commentaire_externe': 'bar',
            },
        )

        self.assertRedirects(response, resolve_url(self.read_path, uuid=self.parcours_doctoral.uuid))
        self.assertNotIn('jury_approval_errors', self.client.session)
        self.parcours_doctoral.refresh_from_db()
        self.assertEqual(self.parcours_doctoral.status, ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE.name)
        actor = JuryActor.objects.get(process=self.parcours_doctoral.jury_group, person=self.adre_manager.person)
        self.assertEqual(actor.state, SignatureState.APPROVED.name)
        self.assertEqual(actor.internal_comment, 'foo')
        self.assertEqual(actor.comment, 'bar')

    def test_post_jury_adre_refus_cdd_user(self):
        url = reverse('parcours_doctoral:update:jury-adre-decision', args=[self.parcours_doctoral.uuid])

        self.client.force_login(user=self.adre_manager.person.user)

        for actor in JuryActor.objects.filter(process=self.parcours_doctoral.jury_group):
            actor.switch_state(SignatureState.APPROVED)
        self.parcours_doctoral.status = ChoixStatutParcoursDoctoral.JURY_APPROUVE_CDD.name
        self.parcours_doctoral.save(update_fields=['status'])

        response = self.client.post(
            url,
            data={
                'decision': DecisionApprovalEnum.DECLINED.name,
                'motif_refus': 'motif',
                'commentaire_interne': 'foo',
                'commentaire_externe': 'bar',
            },
        )

        self.assertRedirects(response, resolve_url(self.read_path, uuid=self.parcours_doctoral.uuid))
        self.assertNotIn('jury_approval_errors', self.client.session)
        self.parcours_doctoral.refresh_from_db()
        self.assertEqual(self.parcours_doctoral.status, ChoixStatutParcoursDoctoral.JURY_REFUSE_ADRE.name)
        actor = JuryActor.objects.get(process=self.parcours_doctoral.jury_group, person=self.adre_manager.person)
        self.assertEqual(actor.state, SignatureState.DECLINED.name)
        self.assertEqual(actor.rejection_reason, 'motif')
        self.assertEqual(actor.internal_comment, 'foo')
        self.assertEqual(actor.comment, 'bar')
