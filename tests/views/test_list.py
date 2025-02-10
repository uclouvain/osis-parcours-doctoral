# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.core.cache import cache
from django.core.exceptions import NON_FIELD_ERRORS
from django.forms import MultipleHiddenInput
from django.shortcuts import reverse
from django.test import RequestFactory, TestCase, override_settings
from django.utils.translation import gettext

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixTypeAdmission,
)
from admission.tests.factories.roles import (
    SicManagementRoleFactory,
)
from base.auth.roles.program_manager import ProgramManager
from base.models.academic_year import AcademicYear
from base.models.enums.entity_type import EntityType
from base.tests import QueriesAssertionsMixin
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import Master120TrainingFactory
from base.tests.factories.entity_version import (
    EntityVersionFactory,
    MainEntityVersionFactory,
)
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.user import UserFactory
from parcours_doctoral.ddd.domain.model.enums import (
    STATUTS_ACTIFS,
    BourseRecherche,
    ChoixCommissionProximiteCDSS,
    ChoixEtapeParcoursDoctoral,
    ChoixStatutParcoursDoctoral,
    ChoixTypeFinancement,
)
from parcours_doctoral.ddd.formation.domain.model.enums import (
    CategorieActivite,
    ContexteFormation,
    StatutActivite,
)
from parcours_doctoral.forms.list import ALL_FEMININE_EMPTY_CHOICE
from parcours_doctoral.models import ParcoursDoctoral
from parcours_doctoral.models.entity_proxy import EntityProxy
from parcours_doctoral.tests.factories.activity import (
    CourseFactory,
    VaeFactory,
)
from parcours_doctoral.tests.factories.confirmation_paper import (
    ConfirmationPaperFactory,
)
from parcours_doctoral.tests.factories.jury import (
    ExternalJuryMemberFactory,
    JuryMemberFactory,
    JuryMemberWithExternalPromoterFactory,
    JuryMemberWithInternalPromoterFactory,
)
from parcours_doctoral.tests.factories.parcours_doctoral import (
    FormationFactory,
    ParcoursDoctoralFactory,
)
from parcours_doctoral.tests.factories.supervision import (
    ExternalPromoterFactory,
    PromoterFactory,
)
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.scholarship import DoctorateScholarshipFactory


@freezegun.freeze_time('2023-01-01')
@override_settings(WAFFLE_CREATE_MISSING_SWITCHES=False)
class ParcoursDoctoralListTestView(QueriesAssertionsMixin, TestCase):
    NB_MAX_QUERIES = 26

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.factory = RequestFactory()

        # Create supervision group members
        cls.promoter = PromoterFactory()

        # Create doctorate
        root_entity = MainEntityVersionFactory(parent=None).entity
        cls.institute = EntityVersionFactory(
            parent=root_entity,
            entity_type=EntityType.INSTITUTE.name,
            acronym='I1',
        )
        cls.other_institute = EntityVersionFactory(
            parent=root_entity,
            entity_type=EntityType.INSTITUTE.name,
            acronym='I2',
        )
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
        cls.commission = EntityVersionFactory(
            parent=cls.sector.entity,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        )
        cls.other_commission = EntityVersionFactory(
            parent=cls.sector.entity,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDSS',
        )
        cls.faculty = EntityVersionFactory(
            parent=cls.sector.entity,
            entity_type=EntityType.FACULTY.name,
            acronym='FAC1',
        )
        cls.other_doctorate_training = FormationFactory(
            acronym='ABCDEF',
            management_entity=cls.other_commission.entity,
            academic_year__year=2023,
            enrollment_campus__name='Mons',
        )
        cls.master_training = Master120TrainingFactory(management_entity=cls.faculty.entity)
        cls.scholarship = DoctorateScholarshipFactory(
            short_name='S2',
        )
        cls.other_scholarship = DoctorateScholarshipFactory(
            short_name='S1',
        )
        cls.doctorate: ParcoursDoctoral = ParcoursDoctoralFactory(
            student__first_name='John',
            student__last_name='Doe',
            training__management_entity=cls.commission.entity,
            training__academic_year__year=2023,
            training__acronym='GHIJKL',
            supervision_group=cls.promoter.process,
            status=ChoixStatutParcoursDoctoral.JURY_APPROUVE_CA.name,
            admission__type=ChoixTypeAdmission.PRE_ADMISSION.name,
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
            is_fnrs_fria_fresh_csc_linked=False,
            financing_comment='Funding comment',
            thesis_institute=cls.institute,
        )
        cls.doctorate_training = cls.doctorate.training
        cls.first_teaching_campus = (
            cls.doctorate.training.educationgroupversion_set.first().root_group.main_teaching_campus
        )
        cls.first_teaching_campus.country = CountryFactory()
        cls.first_teaching_campus.save()

        # Users
        cls.student = cls.doctorate.student

        cls.program_manager = ProgramManagerFactory(education_group=cls.doctorate.training.education_group).person
        ProgramManagerFactory(
            education_group=cls.other_doctorate_training.education_group,
            person=cls.program_manager,
        )
        ProgramManagerFactory(
            education_group=cls.master_training.education_group,
            person=cls.program_manager,
        )
        cls.program_manager_roles = ProgramManager.objects.filter(person=cls.program_manager)

        cls.sic_management = SicManagementRoleFactory().person

        # Academic years
        AcademicYearFactory.produce(base_year=2023, number_past=2, number_future=2)

        # Entities
        faculty_entity = EntityVersionFactory(
            acronym='ABCDEF',
            entity_type=EntityType.FACULTY.name,
            parent=root_entity,
        ).entity

        cls.first_entity = EntityVersionFactory(
            acronym='GHIJK',
            entity_type=EntityType.SCHOOL.name,
            parent=faculty_entity,
        ).entity

        cls.default_params = {
            'annee_academique': 2023,
            'taille_page': 10,
            'date_form-TOTAL_FORMS': 0,
            'date_form-INITIAL_FORMS': 0,
        }

        # Targeted url
        cls.url = reverse('parcours_doctoral:list')

    def setUp(self) -> None:
        cache.clear()

    def _do_request(self, allowed_sql_surplus=0, **data):
        with self.assertNumQueriesLessThan(self.NB_MAX_QUERIES + allowed_sql_surplus, verbose=True):
            return self.client.get(self.url, data={**self.default_params, **data})

    def test_list_user_without_person(self):
        self.client.force_login(user=UserFactory())

        response = self._do_request()
        self.assertEqual(response.status_code, 403)

    def test_list_user_no_role(self):
        self.client.force_login(user=PersonFactory().user)

        response = self._do_request()
        self.assertEqual(response.status_code, 403)

    def test_list_initialization(self):
        self.client.force_login(user=self.program_manager.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['object_list'], [])

        form = response.context['filter_form']

        # annee_academique
        academic_years = AcademicYear.objects.all().order_by('-year').values_list('year', flat=True)
        self.maxDiff = None
        self.assertEqual(form['annee_academique'].value(), 2022)
        self.assertEqual(
            form.fields['annee_academique'].choices, [(year, f'{year}-{str(year + 1)[2:]}') for year in academic_years]
        )

        # numero
        self.assertEqual(form['numero'].value(), None)

        # matricule_doctorant
        self.assertEqual(form['matricule_doctorant'].value(), None)
        self.assertEqual(form.fields['matricule_doctorant'].widget.choices, [])

        # uuid_promoteur
        self.assertEqual(form['uuid_promoteur'].value(), None)
        self.assertEqual(form.fields['uuid_promoteur'].widget.choices, [])

        # uuid_president_jury
        self.assertEqual(form['uuid_president_jury'].value(), None)
        self.assertEqual(form.fields['uuid_president_jury'].widget.choices, [])

        # type_admission
        self.assertEqual(form['type_admission'].value(), None)

        # type_financement
        self.assertEqual(form['type_financement'].value(), None)

        # bourse_recherche
        self.assertEqual(form['bourse_recherche'].value(), None)
        self.assertCountEqual(
            form.fields['bourse_recherche'].choices,
            [
                ALL_FEMININE_EMPTY_CHOICE[0],
                (self.other_scholarship.uuid, self.other_scholarship.short_name),
                (self.scholarship.uuid, self.scholarship.short_name),
                (BourseRecherche.OTHER.name, BourseRecherche.OTHER.value),
            ],
        )

        # fnrs_fria_fresh
        self.assertEqual(form['fnrs_fria_fresh'].value(), None)

        # statuts
        self.assertCountEqual(form['statuts'].value(), STATUTS_ACTIFS)

        # cdds
        self.assertEqual(form['cdds'].value(), None)
        self.assertEqual(
            form.fields['cdds'].choices,
            [
                ('CDA', 'CDA'),
                ('CDSS', 'CDSS'),
            ],
        )
        self.assertNotIsInstance(form.fields['cdds'].widget, MultipleHiddenInput)

        # commission_proximite
        self.assertEqual(form['commission_proximite'].value(), None)
        self.assertCountEqual(
            form.fields['commission_proximite'].choices,
            [
                ALL_FEMININE_EMPTY_CHOICE[0],
                ['CDSS', ChoixCommissionProximiteCDSS.choices()],
            ],
        )

        # sigles_formations
        self.assertEqual(form['sigles_formations'].value(), None)
        self.assertCountEqual(
            form.fields['sigles_formations'].choices,
            [
                (
                    self.doctorate_training.acronym,
                    f'{self.doctorate_training.acronym} - {self.doctorate_training.title}',
                ),
                (
                    self.other_doctorate_training.acronym,
                    f'{self.other_doctorate_training.acronym} - {self.other_doctorate_training.title}',
                ),
            ],
        )

        # instituts_secteurs
        self.assertEqual(form['instituts_secteurs'].value(), None)
        entities = (
            EntityProxy.objects.filter(
                entityversion__entity_type__in=[
                    EntityType.INSTITUTE.name,
                    EntityType.SECTOR.name,
                ],
            )
            .with_acronym()
            .distinct('acronym')
            .values_list('acronym', flat=True)
        )

        self.assertCountEqual(
            form.fields['instituts_secteurs'].choices,
            [(entity_acronym, entity_acronym) for entity_acronym in entities],
        )

        # taille_page
        self.assertEqual(form['taille_page'].value(), 50)

        # page
        self.assertEqual(form['page'].value(), 1)

    def test_dto(self):
        self.client.force_login(user=self.program_manager.user)

        response = self._do_request()

        self.assertEqual(response.status_code, 200)

        results = response.context['object_list']
        self.assertEqual(len(results), 1)

        dto = results[0]

        self.assertEqual(dto.uuid, self.doctorate.uuid)
        self.assertEqual(dto.statut, self.doctorate.status)
        self.assertEqual(dto.reference, f'M-CDA23-{self.doctorate.reference_str}')
        self.assertEqual(dto.matricule_doctorant, self.doctorate.student.global_id)
        self.assertEqual(dto.genre_doctorant, self.doctorate.student.gender)
        self.assertEqual(dto.nom_doctorant, self.doctorate.student.last_name)
        self.assertEqual(dto.prenom_doctorant, self.doctorate.student.first_name)
        self.assertEqual(dto.formation.sigle, self.doctorate.training.acronym)
        self.assertEqual(dto.formation.code, self.doctorate.training.partial_acronym)
        self.assertEqual(dto.formation.annee, self.doctorate.training.academic_year.year)
        self.assertEqual(dto.formation.intitule, self.doctorate.training.title)
        self.assertEqual(dto.formation.intitule_fr, self.doctorate.training.title)
        self.assertEqual(dto.formation.intitule_en, self.doctorate.training.title_english)
        self.assertEqual(dto.formation.type, self.doctorate.training.education_group_type.name)
        self.assertEqual(dto.type_admission, self.doctorate.admission.type)
        self.assertEqual(dto.cree_le, self.doctorate.created_at)
        self.assertEqual(dto.code_bourse, self.doctorate.international_scholarship.short_name)
        self.assertEqual(dto.cotutelle, self.doctorate.cotutelle)
        self.assertEqual(dto.formation_complementaire, False)
        self.assertEqual(dto.en_regle_inscription, False)
        self.assertEqual(dto.total_credits_valides, 0)

    def test_dto_with_complementary_training_activity(self):
        self.client.force_login(user=self.program_manager.user)

        # Add some activities
        activity = CourseFactory(
            parcours_doctoral=self.doctorate,
            context=ContexteFormation.COMPLEMENTARY_TRAINING.name,
            status=StatutActivite.ACCEPTEE.name,
        )

        response = self._do_request()

        results = response.context['object_list']
        self.assertEqual(len(results), 1)

        dto = results[0]

        self.assertEqual(dto.formation_complementaire, True)

        # No complementary training activity

        # Because the context is different
        activity.context = ContexteFormation.DOCTORAL_TRAINING.name
        activity.save()

        response = self._do_request()

        results = response.context['object_list']
        self.assertEqual(len(results), 1)

        dto = results[0]

        self.assertEqual(dto.formation_complementaire, False)

        # Because it's a not completed ucl course
        activity.context = ContexteFormation.COMPLEMENTARY_TRAINING.name
        activity.category = CategorieActivite.UCL_COURSE.name
        activity.course_completed = False
        activity.learning_unit_year = LearningUnitYearFactory()
        activity.save()

        response = self._do_request()

        results = response.context['object_list']
        self.assertEqual(len(results), 1)

        dto = results[0]

        self.assertEqual(dto.formation_complementaire, False)

        activity.course_completed = True
        activity.save()

        response = self._do_request()

        results = response.context['object_list']
        self.assertEqual(len(results), 1)

        dto = results[0]

        self.assertEqual(dto.formation_complementaire, True)

        activity.category = CategorieActivite.COMMUNICATION.name
        activity.course_completed = False
        activity.save()

        response = self._do_request()

        results = response.context['object_list']
        self.assertEqual(len(results), 1)

        dto = results[0]

        self.assertEqual(dto.formation_complementaire, True)

    def test_dto_with_computed_ects_number(self):
        self.client.force_login(user=self.program_manager.user)

        # The sum of the credits only concerned approved activities
        activity = VaeFactory(
            parcours_doctoral=self.doctorate,
            context=ContexteFormation.DOCTORAL_TRAINING.name,
            status=StatutActivite.ACCEPTEE.name,
            ects=10,
        )

        response = self._do_request()

        results = response.context['object_list']
        self.assertEqual(len(results), 1)

        dto = results[0]

        self.assertEqual(dto.total_credits_valides, 10)

        for status in [
            StatutActivite.NON_SOUMISE,
            StatutActivite.SOUMISE,
            StatutActivite.REFUSEE,
        ]:
            activity.status = status.name
            activity.save()

            response = self._do_request()

            results = response.context['object_list']
            self.assertEqual(len(results), 1)

            dto = results[0]

            self.assertEqual(dto.total_credits_valides, 0)

    def test_filter_by_academic_year(self):
        self.client.force_login(user=self.program_manager.user)

        response = self._do_request(annee_academique=2022)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        response = self._do_request(annee_academique=2023)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        # Invalid choice
        response = self._do_request(annee_academique=1)
        form = response.context['form']

        messages = [m.message for m in list(response.context['messages'])]

        self.assertIn(
            f'{gettext("Year")} - {form.fields["annee_academique"].error_messages["invalid_choice"] % {"value": 1}}',
            messages,
        )

    def test_filter_by_reference(self):
        self.client.force_login(user=self.program_manager.user)

        response = self._do_request(numero='12345678')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        response = self._do_request(numero=self.doctorate.reference_str)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

    def test_filter_by_student_global_id(self):
        self.client.force_login(user=self.program_manager.user)

        response = self._do_request(allowed_sql_surplus=1, matricule_doctorant='12345678')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        response = self._do_request(allowed_sql_surplus=1, matricule_doctorant=self.doctorate.student.global_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        form = response.context['form']
        self.assertCountEqual(
            form.fields['matricule_doctorant'].widget.choices,
            [[self.student.global_id, f'{self.student.last_name}, {self.student.first_name}']],
        )

    def test_filter_by_admission_type(self):
        self.client.force_login(user=self.program_manager.user)

        response = self._do_request(type_admission=ChoixTypeAdmission.ADMISSION.name)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        response = self._do_request(type_admission=ChoixTypeAdmission.PRE_ADMISSION.name)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

    def test_filter_by_training(self):
        self.client.force_login(user=self.program_manager.user)

        response = self._do_request(sigles_formations=[self.other_doctorate_training.acronym])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        response = self._do_request(sigles_formations=[self.doctorate_training.acronym])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

    def test_filter_by_status(self):
        self.client.force_login(user=self.program_manager.user)

        response = self._do_request(statuts=[ChoixStatutParcoursDoctoral.ABANDON.name])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        response = self._do_request(statuts=[ChoixStatutParcoursDoctoral.JURY_APPROUVE_CA.name])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

    def test_filter_by_promoter_uuid(self):
        self.client.force_login(user=self.program_manager.user)

        other_promoter = ExternalPromoterFactory()

        response = self._do_request(allowed_sql_surplus=1, uuid_promoteur=other_promoter.uuid)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        form = response.context['form']
        self.assertCountEqual(
            form.fields['uuid_promoteur'].widget.choices,
            [
                [str(other_promoter.uuid), f'{other_promoter.last_name}, {other_promoter.first_name}'],
            ],
        )

        response = self._do_request(allowed_sql_surplus=1, uuid_promoteur=self.promoter.uuid)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        form = response.context['form']
        self.assertCountEqual(
            form.fields['uuid_promoteur'].widget.choices,
            [
                [str(self.promoter.uuid), f'{self.promoter.person.last_name}, {self.promoter.person.first_name}'],
            ],
        )

    def test_filter_by_jury_president_uuid(self):
        self.client.force_login(user=self.program_manager.user)

        external_jury_member = ExternalJuryMemberFactory()

        response = self._do_request(allowed_sql_surplus=1, uuid_president_jury=external_jury_member.uuid)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        form = response.context['form']
        self.assertCountEqual(
            form.fields['uuid_president_jury'].widget.choices,
            [
                [
                    str(external_jury_member.uuid),
                    f'{external_jury_member.last_name}, {external_jury_member.first_name}',
                ],
            ],
        )

        external_promoter_jury_member = JuryMemberWithExternalPromoterFactory()

        response = self._do_request(allowed_sql_surplus=1, uuid_president_jury=external_promoter_jury_member.uuid)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        form = response.context['form']
        self.assertCountEqual(
            form.fields['uuid_president_jury'].widget.choices,
            [
                [
                    str(external_promoter_jury_member.uuid),
                    f'{external_promoter_jury_member.promoter.last_name}, {external_promoter_jury_member.promoter.first_name}',
                ],
            ],
        )

        internal_promoter_jury_member = JuryMemberWithInternalPromoterFactory()

        response = self._do_request(allowed_sql_surplus=1, uuid_president_jury=internal_promoter_jury_member.uuid)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        form = response.context['form']
        self.assertCountEqual(
            form.fields['uuid_president_jury'].widget.choices,
            [
                [
                    str(internal_promoter_jury_member.uuid),
                    f'{internal_promoter_jury_member.promoter.person.last_name}, {internal_promoter_jury_member.promoter.person.first_name}',
                ],
            ],
        )

        internal_jury_member = JuryMemberFactory(parcours_doctoral=self.doctorate)

        response = self._do_request(allowed_sql_surplus=1, uuid_president_jury=internal_jury_member.uuid)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        form = response.context['form']
        self.assertCountEqual(
            form.fields['uuid_president_jury'].widget.choices,
            [
                [
                    str(internal_jury_member.uuid),
                    f'{internal_jury_member.person.last_name}, {internal_jury_member.person.first_name}',
                ],
            ],
        )

    def test_filter_by_cdds(self):
        self.client.force_login(user=self.program_manager.user)

        response = self._do_request(allowed_sql_surplus=1, cdds=[self.other_commission.acronym])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        response = self._do_request(allowed_sql_surplus=1, cdds=[self.commission.acronym])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

    def test_filter_by_institutes_and_sectors(self):
        self.client.force_login(user=self.program_manager.user)

        response = self._do_request(allowed_sql_surplus=1, instituts_secteurs=[self.other_sector.acronym])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        response = self._do_request(allowed_sql_surplus=1, instituts_secteurs=[self.sector.acronym])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        response = self._do_request(allowed_sql_surplus=1, instituts_secteurs=[self.other_institute.acronym])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        response = self._do_request(allowed_sql_surplus=1, instituts_secteurs=[self.institute.acronym])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

    def test_filter_by_financing_type(self):
        self.client.force_login(user=self.program_manager.user)

        response = self._do_request(type_financement=ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        response = self._do_request(type_financement=ChoixTypeFinancement.WORK_CONTRACT.name)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

    def test_filter_by_scholarship(self):
        self.client.force_login(user=self.program_manager.user)

        response = self._do_request(bourse_recherche=BourseRecherche.OTHER.name)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        response = self._do_request(bourse_recherche=str(self.scholarship.uuid))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        response = self._do_request(bourse_recherche=str(self.other_scholarship.uuid))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

    def test_filter_by_fnrs_fria_fresh_criteria(self):
        self.client.force_login(user=self.program_manager.user)

        response = self._do_request(fnrs_fria_fresh=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        response = self._do_request(fnrs_fria_fresh=False)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

    def test_filter_by_invalid_dates(self):
        self.client.force_login(user=self.program_manager.user)

        response = self._do_request(
            **{
                'date_form-TOTAL_FORMS': 1,
                'date_form-0-type_date': ChoixEtapeParcoursDoctoral.ADMISSION.name,
            }
        )

        self.assertEqual(response.status_code, 200)
        date_formset = response.context['date_formset']

        self.assertEqual(date_formset.is_valid(), False)
        self.assertIn(
            gettext('Please select at least one date.'),
            date_formset.forms[0].errors.get(NON_FIELD_ERRORS, []),
        )

        messages = [m.message for m in list(response.context['messages'])]

        self.assertIn(
            f'{gettext("Date - Filter #%s") % 1} - {gettext("Please select at least one date.")}',
            messages,
        )

        response = self._do_request(
            **{
                'date_form-TOTAL_FORMS': 1,
                'date_form-0-type_date': ChoixEtapeParcoursDoctoral.ADMISSION.name,
                'date_form-0-date_debut': '2022-01-02',
                'date_form-0-date_fin': '2021-01-01',
            }
        )

        self.assertEqual(response.status_code, 200)
        date_formset = response.context['date_formset']

        self.assertEqual(date_formset.is_valid(), False)
        self.assertIn(
            gettext("The start date can't be later than the end date"),
            date_formset.forms[0].errors.get(NON_FIELD_ERRORS, []),
        )

        self.assertEqual(len(response.context['object_list']), 0)

    def test_filter_by_admission_date(self):
        self.client.force_login(user=self.program_manager.user)

        response = self._do_request(
            **{
                'date_form-TOTAL_FORMS': 1,
                'date_form-0-type_date': ChoixEtapeParcoursDoctoral.ADMISSION.name,
                'date_form-0-date_debut': '2022-01-01',
                'date_form-0-date_fin': '2022-12-31',
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        response = self._do_request(
            **{
                'date_form-TOTAL_FORMS': 1,
                'date_form-0-type_date': ChoixEtapeParcoursDoctoral.ADMISSION.name,
                'date_form-0-date_debut': '2023-01-01',
                'date_form-0-date_fin': '2023-01-02',
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

    def test_filter_by_confirmation_date(self):
        self.client.force_login(user=self.program_manager.user)

        data = {
            'date_form-TOTAL_FORMS': 1,
            'date_form-0-type_date': ChoixEtapeParcoursDoctoral.CONFIRMATION.name,
            'date_form-0-date_debut': '2024-01-01',
            'date_form-0-date_fin': '2024-01-02',
        }

        # Without confirmation paper -> no result
        response = self._do_request(**data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        # With one confirmation paper but out of range -> no result
        first_confirmation_paper = ConfirmationPaperFactory(
            parcours_doctoral=self.doctorate,
            confirmation_date=datetime.date(2024, 1, 3),
        )

        response = self._do_request(**data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        # With one confirmation paper in range -> one result
        first_confirmation_paper.confirmation_date = datetime.date(2024, 1, 1)
        first_confirmation_paper.save()

        response = self._do_request(**data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

        # With two confirmation papers but the active one is out of range
        first_confirmation_paper.is_active = False
        first_confirmation_paper.save()

        second_confirmation_paper = ConfirmationPaperFactory(
            parcours_doctoral=self.doctorate,
            confirmation_date=datetime.date(2024, 1, 3),
        )

        response = self._do_request(**data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

        # With two confirmation papers and the active one is in range
        second_confirmation_paper.confirmation_date = datetime.date(2024, 1, 2)
        second_confirmation_paper.save()

        response = self._do_request(**data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

    def _test_sort_doctorates(self, field_name, *ordered_doctorates):
        response = self._do_request(o=field_name)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), len(ordered_doctorates))

        doctorate_uuids = [doctorate.uuid for doctorate in ordered_doctorates]
        results_uuids = [result.uuid for result in response.context['object_list']]

        self.assertEqual(doctorate_uuids, results_uuids)

        response = self._do_request(o=f'-{field_name}')

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.context['object_list']), len(ordered_doctorates))

        doctorate_uuids = [doctorate.uuid for doctorate in reversed(ordered_doctorates)]
        results_uuids = [result.uuid for result in response.context['object_list']]

        self.assertEqual(doctorate_uuids, results_uuids)

    def test_sort_by_reference(self):
        self.client.force_login(user=self.program_manager.user)

        other_doctorate = ParcoursDoctoralFactory(
            training=self.other_doctorate_training,
        )

        self._test_sort_doctorates('reference', self.doctorate, other_doctorate)

    def test_sort_by_student_name(self):
        self.client.force_login(user=self.program_manager.user)

        other_doctorate = ParcoursDoctoralFactory(
            training=self.other_doctorate_training,
            student__first_name='Jim',
            student__last_name='Doe',
        )

        self._test_sort_doctorates('nom_etudiant', other_doctorate, self.doctorate)

    def test_sort_by_training(self):
        self.client.force_login(user=self.program_manager.user)

        other_doctorate = ParcoursDoctoralFactory(
            training=self.other_doctorate_training,
        )

        self._test_sort_doctorates('formation', other_doctorate, self.doctorate)

    def test_sort_by_scholarship(self):
        self.client.force_login(user=self.program_manager.user)

        other_doctorate = ParcoursDoctoralFactory(
            training=self.other_doctorate_training,
            international_scholarship=self.other_scholarship,
        )

        self._test_sort_doctorates('bourse', other_doctorate, self.doctorate)

    def test_sort_by_status(self):
        self.client.force_login(user=self.program_manager.user)

        other_doctorate = ParcoursDoctoralFactory(
            training=self.other_doctorate_training,
            status=ChoixStatutParcoursDoctoral.JURY_SOUMIS.name,
        )

        self._test_sort_doctorates('statut', other_doctorate, self.doctorate)

    @freezegun.freeze_time('2022-01-01')
    def test_sort_by_admission_date(self):
        self.client.force_login(user=self.program_manager.user)

        other_doctorate = ParcoursDoctoralFactory(
            training=self.other_doctorate_training,
        )

        self._test_sort_doctorates('date_admission', other_doctorate, self.doctorate)

    def test_sort_by_admission_type(self):
        self.client.force_login(user=self.program_manager.user)

        other_doctorate = ParcoursDoctoralFactory(
            training=self.other_doctorate_training,
            admission__type=ChoixTypeAdmission.ADMISSION.name,
        )

        self._test_sort_doctorates('pre_admission', other_doctorate, self.doctorate)

    def test_sort_by_cotutelle(self):
        self.client.force_login(user=self.program_manager.user)

        other_doctorate = ParcoursDoctoralFactory(
            training=self.other_doctorate_training,
            cotutelle=False,
        )

        self._test_sort_doctorates('cotutelle', other_doctorate, self.doctorate)

    def test_sort_by_additional_training(self):
        self.client.force_login(user=self.program_manager.user)

        CourseFactory(
            parcours_doctoral=self.doctorate,
            context=ContexteFormation.COMPLEMENTARY_TRAINING.name,
            status=StatutActivite.ACCEPTEE.name,
        )

        other_doctorate = ParcoursDoctoralFactory(
            training=self.other_doctorate_training,
        )

        self._test_sort_doctorates('formation_complementaire', other_doctorate, self.doctorate)

    def test_sort_by_credits(self):
        self.client.force_login(user=self.program_manager.user)

        doctorate_activities = [
            CourseFactory(
                parcours_doctoral=self.doctorate,
                status=StatutActivite.ACCEPTEE.name,
                ects=20,
            )
            for _ in range(3)
        ]

        other_doctorate = ParcoursDoctoralFactory(
            training=self.other_doctorate_training,
            international_scholarship=self.other_scholarship,
        )

        other_doctorate_activities = [
            CourseFactory(
                parcours_doctoral=other_doctorate,
                status=StatutActivite.ACCEPTEE.name,
                ects=5,
            )
            for _ in range(5)
        ]

        self._test_sort_doctorates('total_credits_valides', other_doctorate, self.doctorate)

    def test_sorted_uuid_list(self):
        self.client.force_login(user=self.program_manager.user)

        other_doctorate = ParcoursDoctoralFactory(
            training=self.other_doctorate_training,
            student__first_name='Jim',
            student__last_name='Doe',
        )

        response = self._do_request(o='nom_etudiant')

        self.assertEqual(response.status_code, 200)

        object_list = response.context['object_list']

        self.assertEqual(len(object_list), 2)
        self.assertEqual(object_list[0].uuid, other_doctorate.uuid)
        self.assertEqual(object_list[1].uuid, self.doctorate.uuid)

        cached_sorted_list = response.context['view'].object_list.sorted_elements

        self.assertEqual(len(cached_sorted_list), 2)

        self.assertEqual(
            cached_sorted_list[other_doctorate.uuid],
            {
                'previous': None,
                'next': self.doctorate.uuid,
            },
        )

        self.assertEqual(
            cached_sorted_list[self.doctorate.uuid],
            {
                'previous': other_doctorate.uuid,
                'next': None,
            },
        )
