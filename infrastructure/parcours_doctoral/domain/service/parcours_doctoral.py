# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Dict

from admission.ddd.admission.doctorat.preparation.domain.model.proposition import (
    Proposition,
)
from admission.models import DoctorateAdmission, SupervisionActor
from admission.models.enums.actor_type import ActorType as AdmissionActorType
from django.db import transaction
from osis_document.api.utils import documents_remote_duplicate
from osis_signature.enums import SignatureState
from osis_signature.models import Process, StateHistory

from parcours_doctoral.auth.roles.ca_member import CommitteeMember
from parcours_doctoral.auth.roles.promoter import Promoter
from parcours_doctoral.auth.roles.student import Student
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.domain.service.i_parcours_doctoral import (
    IParcoursDoctoralService,
)
from parcours_doctoral.models.actor import ParcoursDoctoralSupervisionActor
from parcours_doctoral.models.parcours_doctoral import (
    ParcoursDoctoral as ParcoursDoctoralModel,
)


class ParcoursDoctoralService(IParcoursDoctoralService):
    FILES_FIELDS = [
        'project_document',
        'gantt_graph',
        'program_proposition',
        'additional_training_project',
        'recommendation_letters',
        'cotutelle_opening_request',
        'cotutelle_convention',
        'cotutelle_other_documents',
        'scholarship_proof',
    ]

    @classmethod
    def _duplicate_supervision_group(cls, admission: DoctorateAdmission) -> Process:
        process = Process.objects.create()
        states = []
        for admission_actor in SupervisionActor.objects.select_related('person', 'country').filter(
            process__uuid=admission.supervision_group.uuid,
        ):
            actor = ParcoursDoctoralSupervisionActor.objects.create(
                process=process,
                person=admission_actor.person,
                first_name=admission_actor.first_name if not admission_actor.person else '',
                last_name=admission_actor.last_name if not admission_actor.person else '',
                email=admission_actor.email if not admission_actor.person else '',
                institute=admission_actor.institute if not admission_actor.person else '',
                city=admission_actor.city if not admission_actor.person else '',
                country=admission_actor.country if not admission_actor.person else None,
                language=admission_actor.language if not admission_actor.person else '',
                type=admission_actor.type,
                is_doctor=admission_actor.is_doctor,
                is_reference_promoter=admission_actor.is_reference_promoter,
                # # TODO À dupliquer ?
                # internal_comment=admission_actor.internal_comment,
                # comment=admission_actor.comment,
            )
            states.append(StateHistory(actor=actor, state=SignatureState.APPROVED.name))
        StateHistory.objects.bulk_create(states)
        return process

    @classmethod
    def _duplicate_roles(cls, admission: DoctorateAdmission) -> None:
        if not Student.objects.filter(person=admission.candidate).exists():
            Student.objects.create(person=admission.candidate)

        promoters = []
        ca_members = []
        for admission_actor in SupervisionActor.objects.select_related('person', 'country').filter(
            process__uuid=admission.supervision_group.uuid,
        ):
            if admission_actor.type == AdmissionActorType.PROMOTER.name:
                promoters.append(Promoter(person=admission_actor.person))
            else:
                ca_members.append(CommitteeMember(person=admission_actor.person))
        Promoter.objects.bulk_create(promoters)
        CommitteeMember.objects.bulk_create(ca_members)

    @classmethod
    def _duplicate_uploaded_files(
        cls, admission: DoctorateAdmission, parcours_doctoral: ParcoursDoctoralModel
    ) -> Dict[str, str]:
        files_uuids = [getattr(admission, field)[0] for field in cls.FILES_FIELDS if getattr(admission, field)]
        uploaded_paths = {
            # TODO Better path name?
            str(
                file_uuid
            ): f'parcours_doctoral/{admission.candidate.uuid}/{parcours_doctoral.uuid}/duplicates_from_admission/'
            for file_uuid in files_uuids
        }

        return documents_remote_duplicate(
            uuids=files_uuids,
            upload_path_by_uuid=uploaded_paths,
        )

    @classmethod
    @transaction.atomic
    def initier(cls, proposition: 'Proposition') -> ParcoursDoctoralIdentity:
        admission: DoctorateAdmission = DoctorateAdmission.objects.get(uuid=proposition.entity_id.uuid)

        supervision_group = cls._duplicate_supervision_group(admission)
        cls._duplicate_roles(admission)

        parcours_doctoral = ParcoursDoctoralModel.objects.create(
            admission=admission,
            reference=admission.reference,
            student=admission.candidate,
            training=admission.training,
            project_title=admission.project_title,
            project_abstract=admission.project_abstract,
            thesis_language=admission.thesis_language,
            thesis_institute=admission.thesis_institute,
            thesis_location=admission.thesis_location,
            phd_alread_started=admission.phd_alread_started,
            phd_alread_started_institute=admission.phd_alread_started_institute,
            work_start_date=admission.work_start_date,
            phd_already_done=admission.phd_already_done,
            phd_already_done_institution=admission.phd_already_done_institution,
            phd_already_done_thesis_domain=admission.phd_already_done_thesis_domain,
            phd_already_done_defense_date=admission.phd_already_done_defense_date,
            phd_already_done_no_defense_reason=admission.phd_already_done_no_defense_reason,
            cotutelle=admission.cotutelle,
            cotutelle_motivation=admission.cotutelle_motivation,
            cotutelle_institution_fwb=admission.cotutelle_institution_fwb,
            cotutelle_institution=admission.cotutelle_institution,
            cotutelle_other_institution_name=admission.cotutelle_other_institution_name,
            cotutelle_other_institution_address=admission.cotutelle_other_institution_address,
            financing_type=admission.financing_type,
            other_international_scholarship=admission.other_international_scholarship,
            international_scholarship=admission.international_scholarship,
            supervision_group=supervision_group,
            proximity_commission=admission.proximity_commission,
            financing_work_contract=admission.financing_work_contract,
            financing_eft=admission.financing_eft,
            scholarship_start_date=admission.scholarship_start_date,
            scholarship_end_date=admission.scholarship_end_date,
            planned_duration=admission.planned_duration,
            dedicated_time=admission.dedicated_time,
            is_fnrs_fria_fresh_csc_linked=admission.is_fnrs_fria_fresh_csc_linked,
            financing_comment=admission.financing_comment,
        )

        uploaded_files = cls._duplicate_uploaded_files(admission, parcours_doctoral)
        for field in cls.FILES_FIELDS:
            try:
                file_uuid = str(getattr(admission, field)[0])
            except IndexError:
                continue
            setattr(parcours_doctoral, field, uploaded_files.get(file_uuid))
        parcours_doctoral.save(update_fields=cls.FILES_FIELDS)

        return ParcoursDoctoralIdentity(uuid=str(parcours_doctoral.uuid))
