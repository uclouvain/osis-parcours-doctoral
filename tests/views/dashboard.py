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
from admission.tests.factories import DoctorateAdmissionFactory
from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.domain.model.enums import (
    ChoixStatutParcoursDoctoral,
)
from parcours_doctoral.ddd.read_view.dto.tableau_bord import TableauBordDTO
from parcours_doctoral.ddd.read_view.queries import RecupererInformationsTableauBordQuery
from parcours_doctoral.tests.factories.confirmation_paper import ConfirmationPaperFactory
from parcours_doctoral.tests.factories.parcours_doctoral import ParcoursDoctoralFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class DashboardCommandTestCase(TestCase):
    def setUp(self):
        # Mock documents
        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("osis_document.api.utils.get_remote_metadata", return_value={"name": "myfile", "size": 1})
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

    @classmethod
    def setUpTestData(cls):
        cls.file_uuid = str(uuid.uuid4())

    @classmethod
    def get_dashboard(cls) -> TableauBordDTO:
        return message_bus_instance.invoke(
            RecupererInformationsTableauBordQuery(),
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

    def assert_dashboard_value(self, category, indicator, value):
        dashboard = self.get_dashboard()
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
