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
from typing import Dict, List
from unittest.mock import patch

import freezegun
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixCommissionProximiteCDSS,
    ChoixDoctoratDejaRealise,
    ChoixStatutPropositionDoctorale,
    ChoixTypeAdmission,
    ChoixTypeContratTravail,
    ChoixTypeFinancement,
)
from admission.tests.factories.doctorate import (
    DoctorateAdmissionFactory,
    DoctorateFactory,
)
from admission.tests.factories.supervision import (
    CaMemberFactory,
    ExternalPromoterFactory,
    PromoterFactory,
)
from base.forms.utils.file_field import PDF_MIME_TYPE
from base.models.enums.entity_type import EntityType
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from infrastructure.messages_bus import message_bus_instance
from parcours_doctoral.ddd.commands import InitialiserParcoursDoctoralCommand
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.ddd.jury.domain.model.enums import FormuleDefense
from parcours_doctoral.models import (
    ActorType,
    ConfirmationPaper,
    ParcoursDoctoral,
    ParcoursDoctoralSupervisionActor,
)
from reference.tests.factories.language import LanguageFactory
from reference.tests.factories.scholarship import ErasmusMundusScholarshipFactory


@freezegun.freeze_time('2023-01-01')
class DoctorateInitializationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student = PersonFactory()
        root = EntityVersionFactory(parent=None).entity
        cls.sector = EntityVersionFactory(
            parent=root,
            entity_type=EntityType.SECTOR.name,
            acronym='SST',
        ).entity
        cls.commission = EntityVersionFactory(
            parent=cls.sector,
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDSS',
        ).entity
        cls.doctorate = DoctorateFactory(
            management_entity=cls.commission,
            enrollment_campus__name='Mons',
        )
        cls.scholarship = ErasmusMundusScholarshipFactory()
        cls.other_scholarship = ErasmusMundusScholarshipFactory()
        cls.language = LanguageFactory(code='EN')
        cls.other_language = LanguageFactory(code='FR')

        cls.documents_names = [
            'scholarship_proof',
            'project_document',
            'gantt_graph',
            'program_proposition',
            'additional_training_project',
            'recommendation_letters',
            'cotutelle_opening_request',
            'cotutelle_convention',
            'cotutelle_other_documents',
        ]

        cls.documents_tokens: Dict[str, List[uuid.UUID]] = {}
        cls.duplicated_documents_tokens: Dict[str, List[uuid.UUID]] = {}
        cls.duplicated_documents_tokens_by_uuid: Dict[str, str] = {}

        for document_name in cls.documents_names:
            cls.documents_tokens[document_name] = [uuid.uuid4()]
            cls.duplicated_documents_tokens[document_name] = [uuid.uuid4()]
            cls.duplicated_documents_tokens_by_uuid[str(cls.documents_tokens[document_name][0])] = str(
                cls.duplicated_documents_tokens[document_name][0],
            )

        cls.pre_existing_promoter = PromoterFactory(
            is_reference_promoter=True,
            internal_comment='Internal comment 1',
            comment='Comment 1',
            pdf_from_candidate=[uuid.uuid4()],
            rejection_reason='R1',
        )
        cls.pre_external_promoter = ExternalPromoterFactory(
            process=cls.pre_existing_promoter.process,
            internal_comment='Internal comment 2',
            comment='Comment 2',
            pdf_from_candidate=[uuid.uuid4()],
            rejection_reason='R2',
        )
        cls.pre_existing_ca_member = CaMemberFactory(
            process=cls.pre_existing_promoter.process,
            internal_comment='Internal comment 3',
            comment='Comment 3',
            pdf_from_candidate=[uuid.uuid4()],
            rejection_reason='R3',
        )

        cls.pre_admission = DoctorateAdmissionFactory(
            candidate=cls.student,
            training=cls.doctorate,
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
            status=ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name,
            supervision_group=cls.pre_existing_promoter.process,
            comment='Comment',
            proximity_commission=ChoixCommissionProximiteCDSS.ECLI.name,
            financing_type=ChoixTypeFinancement.WORK_CONTRACT.name,
            financing_work_contract=ChoixTypeContratTravail.UCLOUVAIN_SCIENTIFIC_STAFF.name,
            financing_eft=10,
            international_scholarship_id=cls.scholarship.pk,
            other_international_scholarship='Other scholarship',
            scholarship_start_date=datetime.date(2020, 1, 1),
            scholarship_end_date=datetime.date(2021, 2, 1),
            scholarship_proof=cls.documents_tokens['scholarship_proof'],
            planned_duration=10,
            dedicated_time=12,
            is_fnrs_fria_fresh_csc_linked=True,
            financing_comment='Financing comment',
            project_title='Project title',
            project_abstract='Project abstract',
            thesis_language=cls.language,
            thesis_institute=EntityVersionFactory(),
            thesis_location='Thesis location',
            phd_alread_started=True,
            phd_alread_started_institute='PHD already started institute',
            work_start_date=datetime.date(2022, 1, 1),
            project_document=cls.documents_tokens['project_document'],
            gantt_graph=cls.documents_tokens['gantt_graph'],
            program_proposition=cls.documents_tokens['program_proposition'],
            additional_training_project=cls.documents_tokens['additional_training_project'],
            recommendation_letters=cls.documents_tokens['recommendation_letters'],
            phd_already_done=ChoixDoctoratDejaRealise.YES.name,
            phd_already_done_institution='PhD already done institution',
            phd_already_done_thesis_domain='PhD already done thesis domain',
            phd_already_done_defense_date=datetime.date(2023, 1, 1),
            phd_already_done_no_defense_reason='No defense reason',
            cotutelle=True,
            cotutelle_motivation='Motivation',
            cotutelle_institution_fwb=True,
            cotutelle_institution=uuid.uuid4(),
            cotutelle_other_institution_name='Cotutelle institute name',
            cotutelle_other_institution_address='Cotutelle institute address',
            cotutelle_opening_request=cls.documents_tokens['cotutelle_opening_request'],
            cotutelle_convention=cls.documents_tokens['cotutelle_convention'],
            cotutelle_other_documents=cls.documents_tokens['cotutelle_other_documents'],
        )

        cls.existing_promoter = PromoterFactory(
            is_reference_promoter=True,
            internal_comment='Internal comment A',
            comment='Comment A',
            pdf_from_candidate=[uuid.uuid4()],
            rejection_reason='RA',
        )
        cls.external_promoter = ExternalPromoterFactory(
            process=cls.existing_promoter.process,
            internal_comment='Internal comment B',
            comment='Comment B',
            pdf_from_candidate=[uuid.uuid4()],
            rejection_reason='RB',
        )
        cls.existing_ca_member = CaMemberFactory(
            process=cls.existing_promoter.process,
            internal_comment='Internal comment C',
            comment='Comment C',
            pdf_from_candidate=[uuid.uuid4()],
            rejection_reason='RC',
        )

        cls.admission = DoctorateAdmissionFactory(
            candidate=cls.student,
            training=cls.doctorate,
            type=ChoixTypeAdmission.ADMISSION.name,
            status=ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name,
            supervision_group=cls.existing_promoter.process,
            comment='Comment A',
            proximity_commission=ChoixCommissionProximiteCDSS.BCGIM.name,
            financing_type=ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
            financing_work_contract=ChoixTypeContratTravail.OTHER.name,
            financing_eft=20,
            international_scholarship_id=cls.other_scholarship.pk,
            other_international_scholarship='Other scholarship A',
            scholarship_start_date=datetime.date(2020, 1, 2),
            scholarship_end_date=datetime.date(2021, 1, 2),
            scholarship_proof=cls.documents_tokens['scholarship_proof'],
            planned_duration=20,
            dedicated_time=22,
            is_fnrs_fria_fresh_csc_linked=False,
            financing_comment='Financing comment A',
            project_title='Project title A',
            project_abstract='Project abstract A',
            thesis_language=cls.other_language,
            thesis_institute=EntityVersionFactory(),
            thesis_location='Thesis location A',
            phd_alread_started=False,
            phd_alread_started_institute='PHD already started institute A',
            work_start_date=datetime.date(2022, 2, 2),
            project_document=cls.documents_tokens['project_document'],
            gantt_graph=cls.documents_tokens['gantt_graph'],
            program_proposition=cls.documents_tokens['program_proposition'],
            additional_training_project=cls.documents_tokens['additional_training_project'],
            recommendation_letters=cls.documents_tokens['recommendation_letters'],
            phd_already_done=ChoixDoctoratDejaRealise.NO.name,
            phd_already_done_institution='PhD already done institution A',
            phd_already_done_thesis_domain='PhD already done thesis domain A',
            phd_already_done_defense_date=datetime.date(2023, 1, 2),
            phd_already_done_no_defense_reason='No defense reason A',
            cotutelle=False,
            cotutelle_motivation='Motivation A',
            cotutelle_institution_fwb=False,
            cotutelle_institution=uuid.uuid4(),
            cotutelle_other_institution_name='Cotutelle institute name A',
            cotutelle_other_institution_address='Cotutelle institute address A',
            cotutelle_opening_request=cls.documents_tokens['cotutelle_opening_request'],
            cotutelle_convention=cls.documents_tokens['cotutelle_convention'],
            cotutelle_other_documents=cls.documents_tokens['cotutelle_other_documents'],
        )

    def setUp(self):
        self.admission.related_pre_admission = None
        self.admission.save(update_fields=['related_pre_admission'])

        # Mock documents
        patcher = patch('osis_document_components.services.get_remote_tokens')
        patched = patcher.start()
        patched.side_effect = lambda uuids, **kwargs: {uuid: uuid.uuid4() for index, uuid in enumerate(uuids)}
        self.addCleanup(patcher.stop)

        patcher = patch('osis_document_components.services.get_several_remote_metadata')
        patched = patcher.start()
        patched.side_effect = lambda tokens: {
            token: {
                'name': 'myfile',
                'mimetype': PDF_MIME_TYPE,
                'size': 1,
            }
            for token in tokens
        }
        self.addCleanup(patcher.stop)

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

        self.documents_remote_duplicate_patcher = patch(
            'parcours_doctoral.infrastructure.parcours_doctoral.domain.service.parcours_doctoral.documents_remote_duplicate'
        )
        self.documents_remote_duplicate_patched = self.documents_remote_duplicate_patcher.start()
        self.documents_remote_duplicate_patched.return_value = self.duplicated_documents_tokens_by_uuid
        self.addCleanup(self.documents_remote_duplicate_patcher.stop)

    def test_initialization_with_a_pre_admission(self):
        result = message_bus_instance.invoke(
            InitialiserParcoursDoctoralCommand(proposition_uuid=str(self.pre_admission.uuid))
        )

        self.assertEqual(ParcoursDoctoral.objects.all().count(), 1)

        doctorate = ParcoursDoctoral.objects.filter(admission=self.pre_admission).first()

        self.assertIsNotNone(doctorate)

        self.assertEqual(str(doctorate.uuid), result.uuid)
        self.assertEqual(doctorate.admission, self.pre_admission)
        self.assertEqual(doctorate.reference, self.pre_admission.reference)
        self.assertEqual(doctorate.justification, self.pre_admission.comment)
        self.assertEqual(doctorate.student, self.pre_admission.candidate)
        self.assertEqual(doctorate.training, self.pre_admission.training)
        self.assertEqual(doctorate.proximity_commission, self.pre_admission.proximity_commission)
        self.assertEqual(doctorate.status, ChoixStatutParcoursDoctoral.ADMIS.name)
        self.assertEqual(doctorate.project_title, self.pre_admission.project_title)
        self.assertEqual(doctorate.project_abstract, self.pre_admission.project_abstract)
        self.assertEqual(doctorate.thesis_language, self.pre_admission.thesis_language)
        self.assertEqual(doctorate.thesis_institute, self.pre_admission.thesis_institute)
        self.assertEqual(doctorate.thesis_location, self.pre_admission.thesis_location)
        self.assertEqual(doctorate.phd_alread_started, self.pre_admission.phd_alread_started)
        self.assertEqual(doctorate.phd_alread_started_institute, self.pre_admission.phd_alread_started_institute)
        self.assertEqual(doctorate.work_start_date, self.pre_admission.work_start_date)
        self.assertEqual(doctorate.project_document, self.duplicated_documents_tokens['project_document'])
        self.assertEqual(doctorate.gantt_graph, self.duplicated_documents_tokens['gantt_graph'])
        self.assertEqual(doctorate.program_proposition, self.duplicated_documents_tokens['program_proposition'])
        self.assertEqual(
            doctorate.additional_training_project, self.duplicated_documents_tokens['additional_training_project']
        )
        self.assertEqual(doctorate.recommendation_letters, self.duplicated_documents_tokens['recommendation_letters'])
        self.assertEqual(doctorate.phd_already_done, self.pre_admission.phd_already_done)
        self.assertEqual(doctorate.phd_already_done_institution, self.pre_admission.phd_already_done_institution)
        self.assertEqual(doctorate.phd_already_done_thesis_domain, self.pre_admission.phd_already_done_thesis_domain)
        self.assertEqual(doctorate.phd_already_done_defense_date, self.pre_admission.phd_already_done_defense_date)
        self.assertEqual(
            doctorate.phd_already_done_no_defense_reason, self.pre_admission.phd_already_done_no_defense_reason
        )
        self.assertEqual(doctorate.cotutelle, self.pre_admission.cotutelle)
        self.assertEqual(doctorate.cotutelle_motivation, self.pre_admission.cotutelle_motivation)
        self.assertEqual(doctorate.cotutelle_institution_fwb, self.pre_admission.cotutelle_institution_fwb)
        self.assertEqual(doctorate.cotutelle_institution, self.pre_admission.cotutelle_institution)
        self.assertEqual(
            doctorate.cotutelle_other_institution_name, self.pre_admission.cotutelle_other_institution_name
        )
        self.assertEqual(
            doctorate.cotutelle_other_institution_address, self.pre_admission.cotutelle_other_institution_address
        )
        self.assertEqual(
            doctorate.cotutelle_opening_request, self.duplicated_documents_tokens['cotutelle_opening_request']
        )
        self.assertEqual(doctorate.cotutelle_convention, self.duplicated_documents_tokens['cotutelle_convention'])
        self.assertEqual(
            doctorate.cotutelle_other_documents, self.duplicated_documents_tokens['cotutelle_other_documents']
        )
        self.assertEqual(doctorate.financing_type, self.pre_admission.financing_type)
        self.assertEqual(doctorate.other_international_scholarship, self.pre_admission.other_international_scholarship)
        self.assertEqual(doctorate.international_scholarship, self.pre_admission.international_scholarship)
        self.assertEqual(doctorate.financing_work_contract, self.pre_admission.financing_work_contract)
        self.assertEqual(doctorate.financing_eft, self.pre_admission.financing_eft)
        self.assertEqual(doctorate.scholarship_start_date, self.pre_admission.scholarship_start_date)
        self.assertEqual(doctorate.scholarship_end_date, self.pre_admission.scholarship_end_date)
        self.assertEqual(doctorate.scholarship_proof, self.duplicated_documents_tokens['scholarship_proof'])
        self.assertEqual(doctorate.planned_duration, self.pre_admission.planned_duration)
        self.assertEqual(doctorate.dedicated_time, self.pre_admission.dedicated_time)
        self.assertEqual(doctorate.is_fnrs_fria_fresh_csc_linked, self.pre_admission.is_fnrs_fria_fresh_csc_linked)
        self.assertEqual(doctorate.financing_comment, self.pre_admission.financing_comment)

        # Check that no confirmation paper has been created
        self.assertFalse(ConfirmationPaper.objects.filter(parcours_doctoral=doctorate).exists())

        # Check the duplication of the supervision group
        self.assertIsNotNone(doctorate.supervision_group)

        actors = ParcoursDoctoralSupervisionActor.objects.filter(process=doctorate.supervision_group)

        self.assertEqual(len(actors), 3)

        duplicated_external_promoter = actors.filter(type=ActorType.PROMOTER.name, person__isnull=True).first()
        duplicated_existing_promoter = actors.filter(type=ActorType.PROMOTER.name, person__isnull=False).first()
        duplicated_existing_ca_member = actors.filter(type=ActorType.CA_MEMBER.name).first()

        self.assertEqual(duplicated_external_promoter.type, self.pre_external_promoter.type)
        self.assertEqual(duplicated_external_promoter.is_doctor, self.pre_external_promoter.is_doctor)
        self.assertEqual(duplicated_external_promoter.internal_comment, '')
        self.assertEqual(duplicated_external_promoter.pdf_from_candidate, [])
        self.assertEqual(duplicated_external_promoter.is_reference_promoter, False)
        self.assertEqual(duplicated_external_promoter.person, self.pre_external_promoter.person)
        self.assertEqual(duplicated_external_promoter.first_name, self.pre_external_promoter.first_name)
        self.assertEqual(duplicated_external_promoter.last_name, self.pre_external_promoter.last_name)
        self.assertEqual(duplicated_external_promoter.email, self.pre_external_promoter.email)
        self.assertEqual(duplicated_external_promoter.institute, self.pre_external_promoter.institute)
        self.assertEqual(duplicated_external_promoter.city, self.pre_external_promoter.city)
        self.assertEqual(duplicated_external_promoter.country, self.pre_external_promoter.country)
        self.assertEqual(duplicated_external_promoter.language, self.pre_external_promoter.language)
        self.assertEqual(duplicated_external_promoter.comment, '')

        self.assertEqual(duplicated_existing_promoter.type, self.pre_existing_promoter.type)
        self.assertEqual(duplicated_existing_promoter.is_doctor, self.pre_existing_promoter.is_doctor)
        self.assertEqual(duplicated_existing_promoter.internal_comment, '')
        self.assertEqual(duplicated_existing_promoter.pdf_from_candidate, [])
        self.assertEqual(duplicated_existing_promoter.is_reference_promoter, True)
        self.assertEqual(duplicated_existing_promoter.person, self.pre_existing_promoter.person)
        self.assertEqual(duplicated_existing_promoter.first_name, self.pre_existing_promoter.first_name)
        self.assertEqual(duplicated_existing_promoter.last_name, self.pre_existing_promoter.last_name)
        self.assertEqual(duplicated_existing_promoter.email, self.pre_existing_promoter.email)
        self.assertEqual(duplicated_existing_promoter.institute, self.pre_existing_promoter.institute)
        self.assertEqual(duplicated_existing_promoter.city, self.pre_existing_promoter.city)
        self.assertEqual(duplicated_existing_promoter.country, self.pre_existing_promoter.country)
        self.assertEqual(duplicated_existing_promoter.language, self.pre_existing_promoter.language)
        self.assertEqual(duplicated_existing_promoter.comment, '')

        self.assertEqual(duplicated_existing_ca_member.type, self.pre_existing_ca_member.type)
        self.assertEqual(duplicated_existing_ca_member.is_doctor, self.pre_existing_ca_member.is_doctor)
        self.assertEqual(duplicated_existing_ca_member.internal_comment, '')
        self.assertEqual(duplicated_existing_ca_member.pdf_from_candidate, [])
        self.assertEqual(duplicated_existing_ca_member.is_reference_promoter, False)
        self.assertEqual(duplicated_existing_ca_member.person, self.pre_existing_ca_member.person)
        self.assertEqual(duplicated_existing_ca_member.first_name, self.pre_existing_ca_member.first_name)
        self.assertEqual(duplicated_existing_ca_member.last_name, self.pre_existing_ca_member.last_name)
        self.assertEqual(duplicated_existing_ca_member.email, self.pre_existing_ca_member.email)
        self.assertEqual(duplicated_existing_ca_member.institute, self.pre_existing_ca_member.institute)
        self.assertEqual(duplicated_existing_ca_member.city, self.pre_existing_ca_member.city)
        self.assertEqual(duplicated_existing_ca_member.country, self.pre_existing_ca_member.country)
        self.assertEqual(duplicated_existing_ca_member.language, self.pre_existing_ca_member.language)
        self.assertEqual(duplicated_existing_ca_member.comment, '')

    def test_initialization_with_an_admission(self):
        result = message_bus_instance.invoke(
            InitialiserParcoursDoctoralCommand(proposition_uuid=str(self.admission.uuid))
        )

        self.assertEqual(ParcoursDoctoral.objects.all().count(), 1)

        doctorate = ParcoursDoctoral.objects.filter(admission=self.admission).first()

        self.assertIsNotNone(doctorate)

        self.assertEqual(str(doctorate.uuid), result.uuid)
        self.assertEqual(doctorate.admission, self.admission)
        self.assertEqual(doctorate.reference, self.admission.reference)
        self.assertEqual(doctorate.justification, self.admission.comment)
        self.assertEqual(doctorate.student, self.admission.candidate)
        self.assertEqual(doctorate.training, self.admission.training)
        self.assertEqual(doctorate.proximity_commission, self.admission.proximity_commission)
        self.assertEqual(doctorate.status, ChoixStatutParcoursDoctoral.ADMIS.name)
        self.assertEqual(doctorate.project_title, self.admission.project_title)
        self.assertEqual(doctorate.project_abstract, self.admission.project_abstract)
        self.assertEqual(doctorate.thesis_language, self.admission.thesis_language)
        self.assertEqual(doctorate.thesis_institute, self.admission.thesis_institute)
        self.assertEqual(doctorate.thesis_location, self.admission.thesis_location)
        self.assertEqual(doctorate.phd_alread_started, self.admission.phd_alread_started)
        self.assertEqual(doctorate.phd_alread_started_institute, self.admission.phd_alread_started_institute)
        self.assertEqual(doctorate.work_start_date, self.admission.work_start_date)
        self.assertEqual(doctorate.project_document, self.duplicated_documents_tokens['project_document'])
        self.assertEqual(doctorate.gantt_graph, self.duplicated_documents_tokens['gantt_graph'])
        self.assertEqual(doctorate.program_proposition, self.duplicated_documents_tokens['program_proposition'])
        self.assertEqual(
            doctorate.additional_training_project, self.duplicated_documents_tokens['additional_training_project']
        )
        self.assertEqual(doctorate.recommendation_letters, self.duplicated_documents_tokens['recommendation_letters'])
        self.assertEqual(doctorate.phd_already_done, self.admission.phd_already_done)
        self.assertEqual(doctorate.phd_already_done_institution, self.admission.phd_already_done_institution)
        self.assertEqual(doctorate.phd_already_done_thesis_domain, self.admission.phd_already_done_thesis_domain)
        self.assertEqual(doctorate.phd_already_done_defense_date, self.admission.phd_already_done_defense_date)
        self.assertEqual(
            doctorate.phd_already_done_no_defense_reason, self.admission.phd_already_done_no_defense_reason
        )
        self.assertEqual(doctorate.cotutelle, self.admission.cotutelle)
        self.assertEqual(doctorate.cotutelle_motivation, self.admission.cotutelle_motivation)
        self.assertEqual(doctorate.cotutelle_institution_fwb, self.admission.cotutelle_institution_fwb)
        self.assertEqual(doctorate.cotutelle_institution, self.admission.cotutelle_institution)
        self.assertEqual(doctorate.cotutelle_other_institution_name, self.admission.cotutelle_other_institution_name)
        self.assertEqual(
            doctorate.cotutelle_other_institution_address, self.admission.cotutelle_other_institution_address
        )
        self.assertEqual(
            doctorate.cotutelle_opening_request, self.duplicated_documents_tokens['cotutelle_opening_request']
        )
        self.assertEqual(doctorate.cotutelle_convention, self.duplicated_documents_tokens['cotutelle_convention'])
        self.assertEqual(
            doctorate.cotutelle_other_documents, self.duplicated_documents_tokens['cotutelle_other_documents']
        )
        self.assertEqual(doctorate.financing_type, self.admission.financing_type)
        self.assertEqual(doctorate.other_international_scholarship, self.admission.other_international_scholarship)
        self.assertEqual(doctorate.international_scholarship, self.admission.international_scholarship)
        self.assertEqual(doctorate.financing_work_contract, self.admission.financing_work_contract)
        self.assertEqual(doctorate.financing_eft, self.admission.financing_eft)
        self.assertEqual(doctorate.scholarship_start_date, self.admission.scholarship_start_date)
        self.assertEqual(doctorate.scholarship_end_date, self.admission.scholarship_end_date)
        self.assertEqual(doctorate.scholarship_proof, self.duplicated_documents_tokens['scholarship_proof'])
        self.assertEqual(doctorate.planned_duration, self.admission.planned_duration)
        self.assertEqual(doctorate.dedicated_time, self.admission.dedicated_time)
        self.assertEqual(doctorate.is_fnrs_fria_fresh_csc_linked, self.admission.is_fnrs_fria_fresh_csc_linked)
        self.assertEqual(doctorate.financing_comment, self.admission.financing_comment)

        # Check that a confirmation paper has been created
        confirmation_paper = ConfirmationPaper.objects.filter(parcours_doctoral=doctorate).first()
        self.assertIsNotNone(confirmation_paper)

        self.assertEqual(confirmation_paper.confirmation_deadline, datetime.date(2025, 1, 1))

        # Check the duplication of the supervision group
        self.assertIsNotNone(doctorate.supervision_group)

        actors = ParcoursDoctoralSupervisionActor.objects.filter(process=doctorate.supervision_group)

        self.assertEqual(len(actors), 3)

        duplicated_external_promoter = actors.filter(type=ActorType.PROMOTER.name, person__isnull=True).first()
        duplicated_existing_promoter = actors.filter(type=ActorType.PROMOTER.name, person__isnull=False).first()
        duplicated_existing_ca_member = actors.filter(type=ActorType.CA_MEMBER.name).first()

        self.assertEqual(duplicated_external_promoter.type, self.external_promoter.type)
        self.assertEqual(duplicated_external_promoter.is_doctor, self.external_promoter.is_doctor)
        self.assertEqual(duplicated_external_promoter.internal_comment, '')
        self.assertEqual(duplicated_external_promoter.pdf_from_candidate, [])
        self.assertEqual(duplicated_external_promoter.is_reference_promoter, False)
        self.assertEqual(duplicated_external_promoter.person, self.external_promoter.person)
        self.assertEqual(duplicated_external_promoter.first_name, self.external_promoter.first_name)
        self.assertEqual(duplicated_external_promoter.last_name, self.external_promoter.last_name)
        self.assertEqual(duplicated_external_promoter.email, self.external_promoter.email)
        self.assertEqual(duplicated_external_promoter.institute, self.external_promoter.institute)
        self.assertEqual(duplicated_external_promoter.city, self.external_promoter.city)
        self.assertEqual(duplicated_external_promoter.country, self.external_promoter.country)
        self.assertEqual(duplicated_external_promoter.language, self.external_promoter.language)
        self.assertEqual(duplicated_external_promoter.comment, '')

        self.assertEqual(duplicated_existing_promoter.type, self.existing_promoter.type)
        self.assertEqual(duplicated_existing_promoter.is_doctor, self.existing_promoter.is_doctor)
        self.assertEqual(duplicated_existing_promoter.internal_comment, '')
        self.assertEqual(duplicated_existing_promoter.pdf_from_candidate, [])
        self.assertEqual(duplicated_existing_promoter.is_reference_promoter, True)
        self.assertEqual(duplicated_existing_promoter.person, self.existing_promoter.person)
        self.assertEqual(duplicated_existing_promoter.first_name, self.existing_promoter.first_name)
        self.assertEqual(duplicated_existing_promoter.last_name, self.existing_promoter.last_name)
        self.assertEqual(duplicated_existing_promoter.email, self.existing_promoter.email)
        self.assertEqual(duplicated_existing_promoter.institute, self.existing_promoter.institute)
        self.assertEqual(duplicated_existing_promoter.city, self.existing_promoter.city)
        self.assertEqual(duplicated_existing_promoter.country, self.existing_promoter.country)
        self.assertEqual(duplicated_existing_promoter.language, self.existing_promoter.language)
        self.assertEqual(duplicated_existing_promoter.comment, '')

        self.assertEqual(duplicated_existing_ca_member.type, self.existing_ca_member.type)
        self.assertEqual(duplicated_existing_ca_member.is_doctor, self.existing_ca_member.is_doctor)
        self.assertEqual(duplicated_existing_ca_member.internal_comment, '')
        self.assertEqual(duplicated_existing_ca_member.pdf_from_candidate, [])
        self.assertEqual(duplicated_existing_ca_member.is_reference_promoter, False)
        self.assertEqual(duplicated_existing_ca_member.person, self.existing_ca_member.person)
        self.assertEqual(duplicated_existing_ca_member.first_name, self.existing_ca_member.first_name)
        self.assertEqual(duplicated_existing_ca_member.last_name, self.existing_ca_member.last_name)
        self.assertEqual(duplicated_existing_ca_member.email, self.existing_ca_member.email)
        self.assertEqual(duplicated_existing_ca_member.institute, self.existing_ca_member.institute)
        self.assertEqual(duplicated_existing_ca_member.city, self.existing_ca_member.city)
        self.assertEqual(duplicated_existing_ca_member.country, self.existing_ca_member.country)
        self.assertEqual(duplicated_existing_ca_member.language, self.existing_ca_member.language)
        self.assertEqual(duplicated_existing_ca_member.comment, '')

    def test_initialization_with_an_admission_following_a_pre_admission(self):
        self.admission.related_pre_admission = self.pre_admission
        self.admission.save(update_fields=['related_pre_admission'])

        original_result = message_bus_instance.invoke(
            InitialiserParcoursDoctoralCommand(proposition_uuid=str(self.pre_admission.uuid))
        )
        self.assertEqual(ParcoursDoctoral.objects.all().count(), 1)

        original_doctorate = ParcoursDoctoral.objects.filter(admission=self.pre_admission).first()
        self.assertIsNotNone(original_doctorate)

        # Check that no confirmation paper has been created
        self.assertFalse(ConfirmationPaper.objects.filter(parcours_doctoral=original_doctorate).exists())

        # Update the doctorate
        original_doctorate.thesis_proposed_title = 'T1'
        original_doctorate.defense_method = FormuleDefense.FORMULE_1.name
        original_doctorate.defense_indicative_date = '2024-01-01'
        original_doctorate.defense_language = self.other_language
        original_doctorate.comment_about_jury = 'C1'
        original_doctorate.accounting_situation = True
        original_doctorate.status = ChoixStatutParcoursDoctoral.JURY_SOUMIS.name
        original_doctorate.save()

        result = message_bus_instance.invoke(
            InitialiserParcoursDoctoralCommand(proposition_uuid=str(self.admission.uuid))
        )

        self.assertEqual(ParcoursDoctoral.objects.all().count(), 1)

        doctorate = ParcoursDoctoral.objects.filter(admission=self.admission).first()

        self.assertIsNotNone(doctorate)

        self.assertEqual(original_doctorate.pk, doctorate.pk)
        self.assertEqual(original_result, result)

        self.assertEqual(str(doctorate.uuid), result.uuid)
        self.assertEqual(doctorate.admission, self.admission)
        self.assertEqual(doctorate.reference, self.admission.reference)
        self.assertEqual(doctorate.justification, self.admission.comment)
        self.assertEqual(doctorate.student, self.admission.candidate)
        self.assertEqual(doctorate.training, self.admission.training)
        self.assertEqual(doctorate.proximity_commission, self.admission.proximity_commission)
        self.assertEqual(doctorate.status, ChoixStatutParcoursDoctoral.ADMIS.name)
        self.assertEqual(doctorate.project_title, self.admission.project_title)
        self.assertEqual(doctorate.project_abstract, self.admission.project_abstract)
        self.assertEqual(doctorate.thesis_language, self.admission.thesis_language)
        self.assertEqual(doctorate.thesis_institute, self.admission.thesis_institute)
        self.assertEqual(doctorate.thesis_location, self.admission.thesis_location)
        self.assertEqual(doctorate.phd_alread_started, self.admission.phd_alread_started)
        self.assertEqual(doctorate.phd_alread_started_institute, self.admission.phd_alread_started_institute)
        self.assertEqual(doctorate.work_start_date, self.admission.work_start_date)
        self.assertEqual(doctorate.project_document, self.duplicated_documents_tokens['project_document'])
        self.assertEqual(doctorate.gantt_graph, self.duplicated_documents_tokens['gantt_graph'])
        self.assertEqual(doctorate.program_proposition, self.duplicated_documents_tokens['program_proposition'])
        self.assertEqual(
            doctorate.additional_training_project, self.duplicated_documents_tokens['additional_training_project']
        )
        self.assertEqual(doctorate.recommendation_letters, self.duplicated_documents_tokens['recommendation_letters'])
        self.assertEqual(doctorate.phd_already_done, self.admission.phd_already_done)
        self.assertEqual(doctorate.phd_already_done_institution, self.admission.phd_already_done_institution)
        self.assertEqual(doctorate.phd_already_done_thesis_domain, self.admission.phd_already_done_thesis_domain)
        self.assertEqual(doctorate.phd_already_done_defense_date, self.admission.phd_already_done_defense_date)
        self.assertEqual(
            doctorate.phd_already_done_no_defense_reason, self.admission.phd_already_done_no_defense_reason
        )
        self.assertEqual(doctorate.cotutelle, self.admission.cotutelle)
        self.assertEqual(doctorate.cotutelle_motivation, self.admission.cotutelle_motivation)
        self.assertEqual(doctorate.cotutelle_institution_fwb, self.admission.cotutelle_institution_fwb)
        self.assertEqual(doctorate.cotutelle_institution, self.admission.cotutelle_institution)
        self.assertEqual(doctorate.cotutelle_other_institution_name, self.admission.cotutelle_other_institution_name)
        self.assertEqual(
            doctorate.cotutelle_other_institution_address, self.admission.cotutelle_other_institution_address
        )
        self.assertEqual(
            doctorate.cotutelle_opening_request, self.duplicated_documents_tokens['cotutelle_opening_request']
        )
        self.assertEqual(doctorate.cotutelle_convention, self.duplicated_documents_tokens['cotutelle_convention'])
        self.assertEqual(
            doctorate.cotutelle_other_documents, self.duplicated_documents_tokens['cotutelle_other_documents']
        )
        self.assertEqual(doctorate.financing_type, self.admission.financing_type)
        self.assertEqual(doctorate.other_international_scholarship, self.admission.other_international_scholarship)
        self.assertEqual(doctorate.international_scholarship, self.admission.international_scholarship)
        self.assertEqual(doctorate.financing_work_contract, self.admission.financing_work_contract)
        self.assertEqual(doctorate.financing_eft, self.admission.financing_eft)
        self.assertEqual(doctorate.scholarship_start_date, self.admission.scholarship_start_date)
        self.assertEqual(doctorate.scholarship_end_date, self.admission.scholarship_end_date)
        self.assertEqual(doctorate.scholarship_proof, self.duplicated_documents_tokens['scholarship_proof'])
        self.assertEqual(doctorate.planned_duration, self.admission.planned_duration)
        self.assertEqual(doctorate.dedicated_time, self.admission.dedicated_time)
        self.assertEqual(doctorate.is_fnrs_fria_fresh_csc_linked, self.admission.is_fnrs_fria_fresh_csc_linked)
        self.assertEqual(doctorate.financing_comment, self.admission.financing_comment)

        # Check that a confirmation paper has been created
        confirmation_paper = ConfirmationPaper.objects.filter(parcours_doctoral=doctorate).first()
        self.assertIsNotNone(confirmation_paper)

        self.assertEqual(confirmation_paper.confirmation_deadline, datetime.date(2025, 1, 1))

        # Check that the doctorate data has not been updated
        self.assertEqual(original_doctorate.thesis_proposed_title, doctorate.thesis_proposed_title)
        self.assertEqual(original_doctorate.defense_method, doctorate.defense_method)
        self.assertEqual(original_doctorate.defense_indicative_date, doctorate.defense_indicative_date)
        self.assertEqual(original_doctorate.defense_language, doctorate.defense_language)
        self.assertEqual(original_doctorate.comment_about_jury, doctorate.comment_about_jury)
        self.assertEqual(original_doctorate.accounting_situation, doctorate.accounting_situation)

        # Check the duplication of the supervision group
        self.assertIsNotNone(doctorate.supervision_group)

        actors = ParcoursDoctoralSupervisionActor.objects.filter(process=doctorate.supervision_group)

        self.assertEqual(len(actors), 3)

        duplicated_external_promoter = actors.filter(type=ActorType.PROMOTER.name, person__isnull=True).first()
        duplicated_existing_promoter = actors.filter(type=ActorType.PROMOTER.name, person__isnull=False).first()
        duplicated_existing_ca_member = actors.filter(type=ActorType.CA_MEMBER.name).first()

        self.assertEqual(duplicated_external_promoter.type, self.external_promoter.type)
        self.assertEqual(duplicated_external_promoter.is_doctor, self.external_promoter.is_doctor)
        self.assertEqual(duplicated_external_promoter.internal_comment, '')
        self.assertEqual(duplicated_external_promoter.pdf_from_candidate, [])
        self.assertEqual(duplicated_external_promoter.is_reference_promoter, False)
        self.assertEqual(duplicated_external_promoter.person, self.external_promoter.person)
        self.assertEqual(duplicated_external_promoter.first_name, self.external_promoter.first_name)
        self.assertEqual(duplicated_external_promoter.last_name, self.external_promoter.last_name)
        self.assertEqual(duplicated_external_promoter.email, self.external_promoter.email)
        self.assertEqual(duplicated_external_promoter.institute, self.external_promoter.institute)
        self.assertEqual(duplicated_external_promoter.city, self.external_promoter.city)
        self.assertEqual(duplicated_external_promoter.country, self.external_promoter.country)
        self.assertEqual(duplicated_external_promoter.language, self.external_promoter.language)
        self.assertEqual(duplicated_external_promoter.comment, '')

        self.assertEqual(duplicated_existing_promoter.type, self.existing_promoter.type)
        self.assertEqual(duplicated_existing_promoter.is_doctor, self.existing_promoter.is_doctor)
        self.assertEqual(duplicated_existing_promoter.internal_comment, '')
        self.assertEqual(duplicated_existing_promoter.pdf_from_candidate, [])
        self.assertEqual(duplicated_existing_promoter.is_reference_promoter, True)
        self.assertEqual(duplicated_existing_promoter.person, self.existing_promoter.person)
        self.assertEqual(duplicated_existing_promoter.first_name, self.existing_promoter.first_name)
        self.assertEqual(duplicated_existing_promoter.last_name, self.existing_promoter.last_name)
        self.assertEqual(duplicated_existing_promoter.email, self.existing_promoter.email)
        self.assertEqual(duplicated_existing_promoter.institute, self.existing_promoter.institute)
        self.assertEqual(duplicated_existing_promoter.city, self.existing_promoter.city)
        self.assertEqual(duplicated_existing_promoter.country, self.existing_promoter.country)
        self.assertEqual(duplicated_existing_promoter.language, self.existing_promoter.language)
        self.assertEqual(duplicated_existing_promoter.comment, '')

        self.assertEqual(duplicated_existing_ca_member.type, self.existing_ca_member.type)
        self.assertEqual(duplicated_existing_ca_member.is_doctor, self.existing_ca_member.is_doctor)
        self.assertEqual(duplicated_existing_ca_member.internal_comment, '')
        self.assertEqual(duplicated_existing_ca_member.pdf_from_candidate, [])
        self.assertEqual(duplicated_existing_ca_member.is_reference_promoter, False)
        self.assertEqual(duplicated_existing_ca_member.person, self.existing_ca_member.person)
        self.assertEqual(duplicated_existing_ca_member.first_name, self.existing_ca_member.first_name)
        self.assertEqual(duplicated_existing_ca_member.last_name, self.existing_ca_member.last_name)
        self.assertEqual(duplicated_existing_ca_member.email, self.existing_ca_member.email)
        self.assertEqual(duplicated_existing_ca_member.institute, self.existing_ca_member.institute)
        self.assertEqual(duplicated_existing_ca_member.city, self.existing_ca_member.city)
        self.assertEqual(duplicated_existing_ca_member.country, self.existing_ca_member.country)
        self.assertEqual(duplicated_existing_ca_member.language, self.existing_ca_member.language)
        self.assertEqual(duplicated_existing_ca_member.comment, '')
