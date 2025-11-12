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

import uuid

import factory

from admission.tests.factories import DoctorateAdmissionFactory
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import TrainingType
from base.models.enums.entity_type import EntityType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity import EntityWithVersionFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.student import StudentFactory
from epc.models.enums.etat_inscription import EtatInscriptionFormation
from epc.tests.factories.inscription_programme_annuel import (
    InscriptionProgrammeAnnuelFactory,
)
from parcours_doctoral.ddd.domain.model.enums import (
    ChoixStatutParcoursDoctoral,
    ChoixTypeFinancement,
)
from parcours_doctoral.models.parcours_doctoral import ParcoursDoctoral
from parcours_doctoral.tests.factories.jury import (
    ExternalJuryActorFactory,
    JuryActorFactory,
    JuryActorWithExternalPromoterFactory,
    JuryActorWithInternalPromoterFactory,
)
from parcours_doctoral.tests.factories.roles import StudentRoleFactory
from parcours_doctoral.tests.factories.supervision import (
    CaMemberFactory,
    ExternalPromoterFactory,
    PromoterFactory,
    _ProcessFactory,
)
from program_management.ddd.domain.program_tree_version import (
    NOT_A_TRANSITION,
    STANDARD,
)
from program_management.tests.factories.education_group_version import (
    EducationGroupVersionFactory,
)


def generate_token():
    from admission.tests.factories import WriteTokenFactory

    return WriteTokenFactory().token


class FormationFactory(EducationGroupYearFactory):
    class Meta:
        model = EducationGroupYear
        django_get_or_create = (
            'education_group',
            'academic_year',
        )

    academic_year = factory.SubFactory(AcademicYearFactory, current=True)
    management_entity = factory.SubFactory(
        EntityWithVersionFactory,
        version__acronym='CDA',
        version__entity_type=EntityType.DOCTORAL_COMMISSION.name,
        version__parent=factory.SubFactory(
            EntityWithVersionFactory,
            version__acronym='SST',
            version__entity_type=EntityType.SECTOR.name,
            version__parent=factory.SubFactory(
                EntityWithVersionFactory,
                version__entity_type=EntityType.SCHOOL.name,
                version__parent=None,
            ),
        ),
    )
    education_group_type = factory.SubFactory(EducationGroupTypeFactory, name=TrainingType.PHD.name)
    primary_language = None

    @factory.post_generation
    def create_related_group_version_factory(self, create, extracted, **kwargs):
        EducationGroupVersionFactory(
            offer=self,
            root_group__academic_year__year=self.academic_year.year,
            version_name=STANDARD,
            transition_name=NOT_A_TRANSITION,
        )


class ParcoursDoctoralFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ParcoursDoctoral

    student = factory.SubFactory(PersonFactory)
    admission = factory.SubFactory(DoctorateAdmissionFactory, admitted=True)
    training = factory.SubFactory(
        FormationFactory,
        enrollment_campus__name='Mons',
    )
    status = ChoixStatutParcoursDoctoral.ADMIS.name
    cotutelle = False
    financing_type = ChoixTypeFinancement.SELF_FUNDING.name
    project_title = 'Test'
    project_abstract = 'Test'
    project_document = factory.LazyFunction(lambda: [uuid.uuid4()])
    program_proposition = factory.LazyFunction(lambda: [uuid.uuid4()])
    additional_training_project = factory.LazyFunction(lambda: [uuid.uuid4()])
    gantt_graph = factory.LazyFunction(lambda: [uuid.uuid4()])
    recommendation_letters = factory.LazyFunction(lambda: [uuid.uuid4()])
    reference = factory.LazyAttribute(lambda obj: obj.admission.reference)
    thesis_institute = factory.SubFactory(EntityVersionFactory)

    @factory.post_generation
    def create_student(self, create, extracted, with_valid_enrolment=True, **kwargs):
        StudentRoleFactory(person=self.student)
        student = StudentFactory(person=self.student)

        if with_valid_enrolment:
            InscriptionProgrammeAnnuelFactory(
                programme__offer=self.training,
                programme_cycle__etudiant=student,
                etat_inscription=EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
            )

    @factory.post_generation
    def create_supervision_group(self, create, extracted, **kwargs):
        if create and not extracted and not self.supervision_group_id:
            process = _ProcessFactory()
            PromoterFactory(actor_ptr__process=process, is_reference_promoter=True)
            ExternalPromoterFactory(actor_ptr__process=process)
            CaMemberFactory(actor_ptr__process=process)
            CaMemberFactory(actor_ptr__process=process)
            self.supervision_group = process

    @factory.post_generation
    def create_jury_group(self, create, extracted, **kwargs):
        if create and not extracted and not self.jury_group_id:
            process = _ProcessFactory()
            JuryActorWithInternalPromoterFactory(process=process)
            JuryActorWithExternalPromoterFactory(process=process)
            JuryActorFactory(process=process)
            JuryActorFactory(process=process)
            ExternalJuryActorFactory(process=process)
            self.jury_group = process

    class Params:
        with_cotutelle = factory.Trait(
            cotutelle=True,
            cotutelle_motivation="Very motivated",
            cotutelle_institution_fwb=False,
            cotutelle_institution="34eab30c-27e3-40db-b92e-0b51546a2448",
            cotutelle_opening_request=factory.LazyFunction(generate_token),
            cotutelle_convention=factory.LazyFunction(generate_token),
            cotutelle_other_documents=factory.LazyFunction(generate_token),
        )
