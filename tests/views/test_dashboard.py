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
import uuid
from unittest import mock
from unittest.mock import patch

import freezegun
from django.db.models.expressions import Value
from django.shortcuts import resolve_url
from django.test import TestCase
from django.test.utils import override_settings

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
    ChoixTypeAdmission,
)
from admission.ddd.admission.doctorat.preparation.read_view.domain.enums.tableau_bord import (
    CategorieTableauBordEnum,
    IndicateurTableauBordEnum,
)
from admission.forms import ALL_FEMININE_EMPTY_CHOICE
from admission.tests.factories import DoctorateAdmissionFactory
from base.models.enums.entity_type import EntityType
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import (
    EntityVersionFactory,
    MainEntityVersionFactory,
)
from base.tests.factories.program_manager import ProgramManagerFactory
from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.domain.model.enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
    ChoixStatutParcoursDoctoral,
)
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ENTITY_CDE,
    ENTITY_CDSS,
    ENTITY_CLSM,
    ENTITY_SCIENCES,
    SIGLE_SCIENCES,
)
from parcours_doctoral.ddd.read_view.dto.tableau_bord import TableauBordDTO
from parcours_doctoral.ddd.read_view.queries import (
    RecupererInformationsTableauBordQuery,
)
from parcours_doctoral.tests.factories.confirmation_paper import (
    ConfirmationPaperFactory,
)
from parcours_doctoral.tests.factories.parcours_doctoral import (
    FormationFactory,
    ParcoursDoctoralFactory,
)
from parcours_doctoral.tests.factories.private_defense import PrivateDefenseFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class DashboardCommandTestCase(TestCase):
    def setUp(self):
        # Mock documents
        patcher = patch("osis_document_components.services.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("osis_document_components.services.get_remote_metadata", return_value={"name": "myfile", "size": 1})
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document_components.services.confirm_remote_upload",
            side_effect=lambda token, *args, **kwargs: token,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document_components.fields.FileField._confirm_multiple_upload",
            side_effect=lambda _, value, __: value,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    @classmethod
    def setUpTestData(cls):
        cls.file_uuid = str(uuid.uuid4())

    @classmethod
    def get_dashboard(cls, **cmd_kwargs) -> TableauBordDTO:
        return message_bus_instance.invoke(
            RecupererInformationsTableauBordQuery(**cmd_kwargs),
        )

    def test_get_dashboard_with_no_admission_and_no_doctorate(self):
        dashboard = self.get_dashboard()

        admission_category = dashboard.categories[CategorieTableauBordEnum.ADMISSION.name]

        self.assertEqual(
            admission_category.indicateurs[IndicateurTableauBordEnum.ADMISSION_AUTORISE_SIC.name].valeur,
            0,
        )

        confirmation_category = dashboard.categories[CategorieTableauBordEnum.CONFIRMATION.name]

        self.assertEqual(
            confirmation_category.indicateurs[IndicateurTableauBordEnum.CONFIRMATION_SOUMISE.name].valeur,
            0,
        )

    def assert_dashboard_value(self, category, indicator, value, **cmd_kwargs):
        dashboard = self.get_dashboard(**cmd_kwargs)
        self.assertEqual(dashboard.categories[category].indicateurs[indicator].valeur, value)

    def test_pre_admission_submitted(self):
        category = CategorieTableauBordEnum.PRE_ADMISSION.name
        indicator = IndicateurTableauBordEnum.PRE_ADMISSION_DOSSIER_SOUMIS.name

        self.assert_dashboard_value(category, indicator, 0)

        admission = DoctorateAdmissionFactory(
            status=ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
        )

        self.assert_dashboard_value(category, indicator, 0)

        admission.status = ChoixStatutPropositionDoctorale.CONFIRMEE.name
        admission.save()

        self.assert_dashboard_value(category, indicator, 1)

        admission.type = ChoixTypeAdmission.ADMISSION.name
        admission.save()

        self.assert_dashboard_value(category, indicator, 0)

    def test_pre_admission_authorized_by_sic(self):
        category = CategorieTableauBordEnum.PRE_ADMISSION.name
        indicator = IndicateurTableauBordEnum.PRE_ADMISSION_AUTORISE_SIC.name

        self.assert_dashboard_value(category, indicator, 0)

        admission = DoctorateAdmissionFactory(
            status=ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
        )

        self.assert_dashboard_value(category, indicator, 0)

        admission.status = ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name
        admission.save()

        self.assert_dashboard_value(category, indicator, 1)

        admission.type = ChoixTypeAdmission.ADMISSION.name
        admission.save()

        self.assert_dashboard_value(category, indicator, 0)

    def test_admission_submitted(self):
        category = CategorieTableauBordEnum.ADMISSION.name
        indicator = IndicateurTableauBordEnum.ADMISSION_DOSSIER_SOUMIS.name

        self.assert_dashboard_value(category, indicator, 0)

        admission = DoctorateAdmissionFactory(
            status=ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
            type=ChoixTypeAdmission.ADMISSION.name,
        )

        self.assert_dashboard_value(category, indicator, 0)

        admission.status = ChoixStatutPropositionDoctorale.CONFIRMEE.name
        admission.save()

        self.assert_dashboard_value(category, indicator, 1)

        admission.type = ChoixTypeAdmission.PRE_ADMISSION.name
        admission.save()

        self.assert_dashboard_value(category, indicator, 0)

    def test_filter_by_proximity_commission(self):
        category = CategorieTableauBordEnum.ADMISSION.name
        indicator = IndicateurTableauBordEnum.ADMISSION_DOSSIER_SOUMIS.name

        admission = DoctorateAdmissionFactory(
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            type=ChoixTypeAdmission.ADMISSION.name,
            proximity_commission=ChoixCommissionProximiteCDSS.DENT.name,
        )

        self.assert_dashboard_value(category, indicator, 1)
        self.assert_dashboard_value(category, indicator, 1, commission_proximite=ChoixCommissionProximiteCDSS.DENT.name)
        self.assert_dashboard_value(category, indicator, 0, commission_proximite=ChoixCommissionProximiteCDSS.ECLI.name)

        category = CategorieTableauBordEnum.CONFIRMATION.name
        indicator = IndicateurTableauBordEnum.CONFIRMATION_SOUMISE.name

        doctorate = ParcoursDoctoralFactory(
            status=ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name,
            proximity_commission=ChoixCommissionProximiteCDSS.DENT.name,
        )

        self.assert_dashboard_value(category, indicator, 1)
        self.assert_dashboard_value(category, indicator, 1, commission_proximite=ChoixCommissionProximiteCDSS.DENT.name)
        self.assert_dashboard_value(category, indicator, 0, commission_proximite=ChoixCommissionProximiteCDSS.ECLI.name)

    def test_filter_by_cdds(self):
        category = CategorieTableauBordEnum.ADMISSION.name
        indicator = IndicateurTableauBordEnum.ADMISSION_DOSSIER_SOUMIS.name

        entity = EntityFactory()
        EntityVersionFactory(
            entity=entity,
            acronym='E1',
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
        )

        admission = DoctorateAdmissionFactory(
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            type=ChoixTypeAdmission.ADMISSION.name,
            training__management_entity=entity,
        )

        self.assert_dashboard_value(category, indicator, 1)
        self.assert_dashboard_value(category, indicator, 1, cdds=['E1'])
        self.assert_dashboard_value(category, indicator, 0, cdds=['E2'])

        category = CategorieTableauBordEnum.CONFIRMATION.name
        indicator = IndicateurTableauBordEnum.CONFIRMATION_SOUMISE.name

        doctorate = ParcoursDoctoralFactory(
            status=ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name,
            training__management_entity=entity,
        )

        self.assert_dashboard_value(category, indicator, 1)
        self.assert_dashboard_value(category, indicator, 1, cdds=['E1'])
        self.assert_dashboard_value(category, indicator, 0, cdds=['E2'])

    def test_admission_authorized_by_sic(self):
        category = CategorieTableauBordEnum.ADMISSION.name
        indicator = IndicateurTableauBordEnum.ADMISSION_AUTORISE_SIC.name

        self.assert_dashboard_value(category, indicator, 0)

        admission = DoctorateAdmissionFactory(
            status=ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
            type=ChoixTypeAdmission.ADMISSION.name,
        )

        self.assert_dashboard_value(category, indicator, 0)

        admission.status = ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name
        admission.save()

        self.assert_dashboard_value(category, indicator, 1)

        admission.type = ChoixTypeAdmission.PRE_ADMISSION.name
        admission.save()

        self.assert_dashboard_value(category, indicator, 0)

    def test_confirmation_submitted(self):
        category = CategorieTableauBordEnum.CONFIRMATION.name
        indicator = IndicateurTableauBordEnum.CONFIRMATION_SOUMISE.name

        self.assert_dashboard_value(category, indicator, 0)

        doctorate = ParcoursDoctoralFactory(status=ChoixStatutParcoursDoctoral.ADMIS.name)

        self.assert_dashboard_value(category, indicator, 0)

        doctorate.status = ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name
        doctorate.save()

        self.assert_dashboard_value(category, indicator, 1)

    def test_confirmation_submitted_with_pv(self):
        category = CategorieTableauBordEnum.CONFIRMATION.name
        indicator = IndicateurTableauBordEnum.CONFIRMATION_PV_TELEVERSE.name

        self.assert_dashboard_value(category, indicator, 0)

        doctorate = ParcoursDoctoralFactory(status=ChoixStatutParcoursDoctoral.ADMIS.name)

        confirmation_paper = ConfirmationPaperFactory(
            parcours_doctoral=doctorate,
            supervisor_panel_report=[self.file_uuid],
            is_active=True,
        )

        self.assert_dashboard_value(category, indicator, 0)

        doctorate.status = ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name
        doctorate.save()

        self.assert_dashboard_value(category, indicator, 1)

        confirmation_paper.supervisor_panel_report = []
        confirmation_paper.save()

        self.assert_dashboard_value(category, indicator, 0)

        confirmation_paper.is_active = False
        confirmation_paper.save()

        new_confirmation_paper = ConfirmationPaperFactory(
            parcours_doctoral=doctorate,
            supervisor_panel_report=[self.file_uuid],
            is_active=True,
        )

        self.assert_dashboard_value(category, indicator, 1)

    def test_confirmation_with_extended_deadline(self):
        category = CategorieTableauBordEnum.CONFIRMATION.name
        indicator = IndicateurTableauBordEnum.CONFIRMATION_REPORT_DATE.name

        self.assert_dashboard_value(category, indicator, 0)

        doctorate = ParcoursDoctoralFactory(status=ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name)

        confirmation_paper = ConfirmationPaperFactory(
            parcours_doctoral=doctorate,
            is_active=True,
            extended_deadline=datetime.date(2025, 1, 1),
        )

        self.assert_dashboard_value(category, indicator, 0)

        doctorate.status = ChoixStatutParcoursDoctoral.ADMIS.name
        doctorate.save()

        self.assert_dashboard_value(category, indicator, 1)

        confirmation_paper.extended_deadline = None
        confirmation_paper.save()

        self.assert_dashboard_value(category, indicator, 0)

        confirmation_paper.is_active = False
        confirmation_paper.save()

        new_confirmation_paper = ConfirmationPaperFactory(
            parcours_doctoral=doctorate,
            extended_deadline=datetime.date(2025, 1, 1),
            is_active=True,
        )

        self.assert_dashboard_value(category, indicator, 1)

    @mock.patch('django.db.models.functions.datetime.Now.resolve_expression')
    def test_confirmation_deadline_two_months(self, mock_resolve):
        category = CategorieTableauBordEnum.CONFIRMATION.name
        indicator = IndicateurTableauBordEnum.CONFIRMATION_ECHEANCE_2_MOIS.name

        # self.assert_dashboard_value(category, indicator, 0)

        # Admission date: 2024/01/01
        # Confirmation deadline date: 2024/12/31
        # Today date: 2024/01/01
        with freezegun.freeze_time(datetime.date(2024, 1, 1)):
            current_date = Value(datetime.date(2024, 1, 1))
            mock_resolve.side_effect = current_date.resolve_expression
            doctorate = ParcoursDoctoralFactory(
                status=ChoixStatutParcoursDoctoral.ADMIS.name,
            )

            confirmation_paper = ConfirmationPaperFactory(
                parcours_doctoral=doctorate,
                is_active=True,
                confirmation_deadline=datetime.date(2024, 12, 31),
            )

            self.assert_dashboard_value(category, indicator, 0)

        # Today date: 2024/09/30
        with freezegun.freeze_time(datetime.date(2024, 9, 30)):
            current_date = Value(datetime.date(2024, 9, 30))
            mock_resolve.side_effect = current_date.resolve_expression

            self.assert_dashboard_value(category, indicator, 0)

        # Today date: 2024/10/01
        with freezegun.freeze_time(datetime.date(2024, 10, 1)):
            current_date = Value(datetime.date(2024, 10, 1))
            mock_resolve.side_effect = current_date.resolve_expression

            self.assert_dashboard_value(category, indicator, 1)

            doctorate.status = ChoixStatutParcoursDoctoral.CONFIRMATION_A_REPRESENTER.name
            doctorate.save()

            self.assert_dashboard_value(category, indicator, 1)

            doctorate.status = ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name
            doctorate.save()

            self.assert_dashboard_value(category, indicator, 0)

            doctorate.status = ChoixStatutParcoursDoctoral.ADMIS.name
            doctorate.save()

            confirmation_paper.is_active = False
            confirmation_paper.save()

            new_confirmation_paper = ConfirmationPaperFactory(
                parcours_doctoral=doctorate,
                is_active=True,
                confirmation_deadline=datetime.date(2025, 1, 31),
            )

            self.assert_dashboard_value(category, indicator, 0)

    def test_jury_ca_approved(self):
        category = CategorieTableauBordEnum.JURY.name
        indicator = IndicateurTableauBordEnum.JURY_VALIDE_CA.name

        self.assert_dashboard_value(category, indicator, 0)

        doctorate = ParcoursDoctoralFactory(status=ChoixStatutParcoursDoctoral.ADMIS.name)

        self.assert_dashboard_value(category, indicator, 0)

        doctorate.status = ChoixStatutParcoursDoctoral.JURY_APPROUVE_CA.name
        doctorate.save()

        self.assert_dashboard_value(category, indicator, 1)

    def test_jury_adre_rejected(self):
        category = CategorieTableauBordEnum.JURY.name
        indicator = IndicateurTableauBordEnum.JURY_REJET_ADRE.name

        self.assert_dashboard_value(category, indicator, 0)

        doctorate = ParcoursDoctoralFactory(status=ChoixStatutParcoursDoctoral.ADMIS.name)

        self.assert_dashboard_value(category, indicator, 0)

        doctorate.status = ChoixStatutParcoursDoctoral.JURY_REFUSE_ADRE.name
        doctorate.save()

        self.assert_dashboard_value(category, indicator, 1)

    def test_jury_adre_approved(self):
        category = CategorieTableauBordEnum.JURY.name
        indicator = IndicateurTableauBordEnum.JURY_VALIDE_ADRE.name

        self.assert_dashboard_value(category, indicator, 0)

        doctorate = ParcoursDoctoralFactory(status=ChoixStatutParcoursDoctoral.ADMIS.name)

        self.assert_dashboard_value(category, indicator, 0)

        doctorate.status = ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE.name
        doctorate.save()

        self.assert_dashboard_value(category, indicator, 1)

    def test_submitted_private_defense_1(self):
        category = CategorieTableauBordEnum.FORMULE_1_DEFENSE_PRIVEE.name
        indicator = IndicateurTableauBordEnum.FORMULE_1_DEFENSE_PRIVEE_SOUMISE.name

        self.assert_dashboard_value(category, indicator, 0)

        doctorate = ParcoursDoctoralFactory(status=ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_AUTORISEE.name)

        self.assert_dashboard_value(category, indicator, 0)

        doctorate.status = ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE.name
        doctorate.save()

        self.assert_dashboard_value(category, indicator, 1)

    def test_submitted_private_defense_1_with_minutes(self):
        category = CategorieTableauBordEnum.FORMULE_1_DEFENSE_PRIVEE.name
        indicator = IndicateurTableauBordEnum.FORMULE_1_DEFENSE_PRIVEE_PV_TELEVERSE.name

        self.assert_dashboard_value(category, indicator, 0)

        doctorate = ParcoursDoctoralFactory(status=ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_AUTORISEE.name)
        private_defense = PrivateDefenseFactory(parcours_doctoral=doctorate)

        self.assert_dashboard_value(category, indicator, 0)

        doctorate.status = ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE.name
        doctorate.save()

        self.assert_dashboard_value(category, indicator, 1)

        private_defense.current_parcours_doctoral = None
        private_defense.save()

        new_private_defense = PrivateDefenseFactory(parcours_doctoral=doctorate, minutes=[])

        self.assert_dashboard_value(category, indicator, 0)


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class DashboardViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.file_uuid = str(uuid.uuid4())

        root_entity = MainEntityVersionFactory(parent=None).entity
        cls.sector = EntityVersionFactory(
            parent=root_entity,
            entity_type=EntityType.SECTOR.name,
            acronym='SST',
        )
        cls.other_sector = EntityVersionFactory(
            parent=root_entity,
            entity_type=EntityType.SECTOR.name,
            acronym='SSH',
        )
        cls.cde_commission = EntityVersionFactory(
            parent=cls.sector.entity,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDE',
        )
        cls.cdss_commission = EntityVersionFactory(
            parent=cls.sector.entity,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDSS',
        )
        cls.clsm_commission = EntityVersionFactory(
            parent=cls.sector.entity,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CLSM',
        )
        cls.cda_commission = EntityVersionFactory(
            parent=cls.sector.entity,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        )
        cls.science_commission = EntityVersionFactory(
            parent=cls.sector.entity,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='SC3DP',
        )
        cls.science_training = FormationFactory(acronym=SIGLE_SCIENCES, management_entity=cls.science_commission.entity)
        cls.cde_training = FormationFactory(management_entity=cls.cde_commission.entity)
        cls.clsm_training = FormationFactory(management_entity=cls.clsm_commission.entity)
        cls.cda_training = FormationFactory(management_entity=cls.cda_commission.entity)
        cls.cdss_training = FormationFactory(management_entity=cls.cdss_commission.entity)

        cls.cda_admission = DoctorateAdmissionFactory(
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            training=cls.cda_training,
        )
        cls.cde_admission = DoctorateAdmissionFactory(
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            training=cls.cde_training,
            proximity_commission=ChoixCommissionProximiteCDEouCLSM.ECONOMY.name,
        )
        cls.cdss_admission = DoctorateAdmissionFactory(
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            training=cls.cdss_training,
            proximity_commission=ChoixCommissionProximiteCDSS.ECLI.name,
        )
        cls.clsm_admission = DoctorateAdmissionFactory(
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            training=cls.clsm_training,
        )
        cls.science_admission = DoctorateAdmissionFactory(
            status=ChoixStatutPropositionDoctorale.CONFIRMEE.name,
            training=cls.science_training,
        )
        cls.cda_doctorate = ParcoursDoctoralFactory(
            status=ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name,
            training=cls.cda_training,
        )
        cls.cde_doctorate = ParcoursDoctoralFactory(
            status=ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name,
            training=cls.cde_training,
            proximity_commission=ChoixCommissionProximiteCDEouCLSM.ECONOMY.name,
        )
        cls.cdss_doctorate = ParcoursDoctoralFactory(
            status=ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name,
            training=cls.cdss_training,
            proximity_commission=ChoixCommissionProximiteCDSS.ECLI.name,
        )
        cls.clsm_doctorate = ParcoursDoctoralFactory(
            status=ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name,
            training=cls.clsm_training,
        )
        cls.science_doctorate = ParcoursDoctoralFactory(
            status=ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name,
            training=cls.science_training,
        )
        cls.url = resolve_url('parcours_doctoral:dashboard')

    def setUp(self):
        # Mock documents
        patcher = patch("osis_document_components.services.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("osis_document_components.services.get_remote_metadata", return_value={"name": "myfile", "size": 1})
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document_components.services.confirm_remote_upload",
            side_effect=lambda token, *args, **kwargs: token,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document_components.fields.FileField._confirm_multiple_upload",
            side_effect=lambda _, value, __: value,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _test_assert_nb_results(self, context, nb_admissions, nb_doctorates):
        self.assertEqual(
            context['dashboard']
            .categories[CategorieTableauBordEnum.ADMISSION.name]
            .indicateurs[IndicateurTableauBordEnum.ADMISSION_DOSSIER_SOUMIS.name]
            .valeur,
            nb_admissions,
        )
        self.assertEqual(
            context['dashboard']
            .categories[CategorieTableauBordEnum.CONFIRMATION.name]
            .indicateurs[IndicateurTableauBordEnum.CONFIRMATION_SOUMISE.name]
            .valeur,
            nb_doctorates,
        )

    def test_get_dashboard_form_and_data(self):
        # CDA
        program_manager = ProgramManagerFactory(education_group=self.cda_training.education_group)

        self.client.force_login(user=program_manager.person.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        # Check form
        form = response.context['form']

        self.assertEqual(form['commission_proximite'].value(), None)
        self.assertEqual(form['cdds'].value(), None)

        proximity_commission_expected_choices = [ALL_FEMININE_EMPTY_CHOICE[0]]
        self.assertEqual(form.fields['commission_proximite'].choices, proximity_commission_expected_choices)

        cdds_commission_expected_choices = [('CDA', 'CDA')]
        self.assertCountEqual(form.fields['cdds'].choices, cdds_commission_expected_choices)

        # Check dashboard
        self._test_assert_nb_results(context=response.context, nb_admissions=1, nb_doctorates=1)

        # CDA + CDE
        ProgramManagerFactory(
            person=program_manager.person,
            education_group=self.cde_training.education_group,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        # Check form
        form = response.context['form']

        proximity_commission_expected_choices.append(
            [f'{ENTITY_CDE} / {ENTITY_CLSM}', ChoixCommissionProximiteCDEouCLSM.choices()]
        )
        self.assertEqual(form.fields['commission_proximite'].choices, proximity_commission_expected_choices)

        cdds_commission_expected_choices.append(('CDE', 'CDE'))
        self.assertCountEqual(form.fields['cdds'].choices, cdds_commission_expected_choices)

        # Check dashboard
        self._test_assert_nb_results(context=response.context, nb_admissions=2, nb_doctorates=2)

        # CDA + CDE + CLSM
        ProgramManagerFactory(
            person=program_manager.person,
            education_group=self.clsm_training.education_group,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        # Check dashboard
        self._test_assert_nb_results(context=response.context, nb_admissions=3, nb_doctorates=3)

        # Check form
        form = response.context['form']

        self.assertEqual(form.fields['commission_proximite'].choices, proximity_commission_expected_choices)

        cdds_commission_expected_choices.append(('CLSM', 'CLSM'))
        self.assertCountEqual(form.fields['cdds'].choices, cdds_commission_expected_choices)

        # CDA + CDE + CLSM + CDSS
        ProgramManagerFactory(
            person=program_manager.person,
            education_group=self.cdss_training.education_group,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        # Check dashboard
        self._test_assert_nb_results(context=response.context, nb_admissions=4, nb_doctorates=4)

        # Check form
        form = response.context['form']

        proximity_commission_expected_choices.append([ENTITY_CDSS, ChoixCommissionProximiteCDSS.choices()])
        self.assertEqual(form.fields['commission_proximite'].choices, proximity_commission_expected_choices)

        cdds_commission_expected_choices.append(('CDSS', 'CDSS'))
        self.assertCountEqual(form.fields['cdds'].choices, cdds_commission_expected_choices)

        # CDA + CDE + CLSM + CDSS + SCIENCE
        ProgramManagerFactory(
            person=program_manager.person,
            education_group=self.science_training.education_group,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        # Check form
        form = response.context['form']

        proximity_commission_expected_choices.append([ENTITY_SCIENCES, ChoixSousDomaineSciences.choices()])
        self.assertEqual(form.fields['commission_proximite'].choices, proximity_commission_expected_choices)

        cdds_commission_expected_choices.append(('SC3DP', 'SC3DP'))
        self.assertCountEqual(form.fields['cdds'].choices, cdds_commission_expected_choices)

        # Check dashboard
        self._test_assert_nb_results(context=response.context, nb_admissions=5, nb_doctorates=5)

    def test_post_dashboard_form(self):
        # CDSS + CDE
        program_manager = ProgramManagerFactory(education_group=self.cdss_training.education_group)
        ProgramManagerFactory(
            person=program_manager.person,
            education_group=self.cde_training.education_group,
        )

        self.client.force_login(user=program_manager.person.user)

        # Don't pass any data -> all the managed cdds are used
        response = self.client.post(self.url, data={})

        self.assertEqual(response.status_code, 200)

        self._test_assert_nb_results(context=response.context, nb_admissions=2, nb_doctorates=2)

        # Filter by CDD
        response = self.client.post(self.url, data={'cdds': ['CDSS', 'CDE']})

        self.assertEqual(response.status_code, 200)

        self._test_assert_nb_results(context=response.context, nb_admissions=2, nb_doctorates=2)

        response = self.client.post(self.url, data={'cdds': ['CDSS']})

        self.assertEqual(response.status_code, 200)

        self._test_assert_nb_results(context=response.context, nb_admissions=1, nb_doctorates=1)

        # Filter by proximity commission
        response = self.client.post(self.url, data={'commission_proximite': ChoixCommissionProximiteCDSS.ECLI.name})

        self.assertEqual(response.status_code, 200)

        self._test_assert_nb_results(context=response.context, nb_admissions=1, nb_doctorates=1)
