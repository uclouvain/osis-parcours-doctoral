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
from unittest.mock import MagicMock

from django.test import TestCase

from parcours_doctoral.ddd.domain.model.enums import ChoixEtapeParcoursDoctoral, ChoixStatutParcoursDoctoral
from parcours_doctoral.templatetags.parcours_doctoral import get_step_status


class GetStepStatusTestCase(TestCase):
    def test_admis_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.ADMIS.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.ADMIS)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_confirmation_soumise_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_confirmation_reussie_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_non_autorise_a_poursuivre_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.ADMIS.NON_AUTORISE_A_POURSUIVRE.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.NON_AUTORISE_A_POURSUIVRE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_confirmation_a_representer_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.ADMIS.CONFIRMATION_A_REPRESENTER.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.CONFIRMATION_A_REPRESENTER)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_jury_soumis_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.JURY_SOUMIS.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.JURY_SOUMIS)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_jury_approuve_ca_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.JURY_APPROUVE_CA.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.JURY_APPROUVE_CA)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_jury_approuve_cdd_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.JURY_APPROUVE_CDD.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.JURY_APPROUVE_CDD)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_jury_refuse_cdd_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.JURY_REFUSE_CDD.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.JURY_REFUSE_CDD)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_jury_approuve_adre_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_jury_refuse_adre_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.JURY_REFUSE_ADRE.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.JURY_REFUSE_ADRE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_recevabilite_soumise_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.RECEVABILITE_SOUMISE.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.RECEVABILITE_SOUMISE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_recevabilite_a_recommencer_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.ADMIS.RECEVABILITE_A_RECOMMENCER.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.RECEVABILITE_A_RECOMMENCER)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_recevabilite_reussie_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.RECEVABILITE_REUSSIE.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.RECEVABILITE_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_recevabilite_en_echec_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.RECEVABILITE_EN_ECHEC.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.RECEVABILITE_EN_ECHEC)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_defense_privee_soumise_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.RECEVABILITE_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_SOUMISE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_defense_privee_autorisee_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_AUTORISEE.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.RECEVABILITE_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_AUTORISEE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_AUTORISEE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_defense_privee_a_recommencer_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_A_RECOMMENCER.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.RECEVABILITE_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_A_RECOMMENCER)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_A_RECOMMENCER)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_defense_privee_reussie_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_REUSSIE.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.RECEVABILITE_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_defense_privee_en_echec_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_EN_ECHEC.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.RECEVABILITE_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_EN_ECHEC)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_EN_ECHEC)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_soutenance_publique_soumise_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.SOUTENANCE_PUBLIQUE_SOUMISE.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.RECEVABILITE_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.SOUTENANCE_PUBLIQUE_SOUMISE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.SOUTENANCE_PUBLIQUE_SOUMISE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_soutenance_publique_autorisee_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.SOUTENANCE_PUBLIQUE_AUTORISEE.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.RECEVABILITE_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.SOUTENANCE_PUBLIQUE_AUTORISEE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.SOUTENANCE_PUBLIQUE_AUTORISEE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_defense_et_soutenance_soumises_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.DEFENSE_ET_SOUTENANCE_SOUMISES.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.RECEVABILITE_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.DEFENSE_ET_SOUTENANCE_SOUMISES)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.DEFENSE_ET_SOUTENANCE_SOUMISES)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.DEFENSE_ET_SOUTENANCE_SOUMISES)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_defense_et_soutenance_autorisees_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.DEFENSE_ET_SOUTENANCE_AUTORISEES.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.RECEVABILITE_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.DEFENSE_ET_SOUTENANCE_AUTORISEES)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.DEFENSE_ET_SOUTENANCE_AUTORISEES)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.DEFENSE_ET_SOUTENANCE_AUTORISEES)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertIsNone(result)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_proclame_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.PROCLAME.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.JURY_APPROUVE_ADRE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.RECEVABILITE_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.DEFENSE_PRIVEE_REUSSIE)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.PROCLAME)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.PROCLAME)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.PROCLAME)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertIsNone(result)

    def test_abandon_status(self):
        doctorate = MagicMock(statut=ChoixStatutParcoursDoctoral.ABANDON.name)

        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.CONFIRMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.ABANDON)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.JURY.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.ABANDON)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DECISION_DE_RECEVABILITE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.ABANDON)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_PRIVEE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.ABANDON)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.SOUTENANCE_PUBLIQUE.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.ABANDON)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.DEFENSE_SOUTENANCE_FORMULE_2.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.ABANDON)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.PROCLAMATION.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.ABANDON)
        result = get_step_status(doctorate=doctorate, step=ChoixEtapeParcoursDoctoral.ABANDON_ECHEC.name)
        self.assertEqual(result, ChoixStatutParcoursDoctoral.ABANDON)
