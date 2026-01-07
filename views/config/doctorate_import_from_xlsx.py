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
import decimal
from datetime import date
from typing import Any, Literal, Optional

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import Exists, F, OuterRef
from django.db.models.fields.tuple_lookups import Tuple
from django.utils.translation import gettext_lazy
from osis_signature.enums import SignatureState
from osis_signature.models import Process, StateHistory
from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError
from pydantic_core.core_schema import ValidationInfo

from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixTypeAdmission
from base.models.education_group_year import EducationGroupYear
from base.models.entity_version import EntityVersion
from base.models.enums.education_group_types import TrainingType
from base.models.person import Person
from base.models.student import Student
from epc.models.inscription_programme_annuel import InscriptionProgrammeAnnuel
from parcours_doctoral.auth.roles.ca_member import CommitteeMember
from parcours_doctoral.auth.roles.promoter import Promoter
from parcours_doctoral.ddd.domain.model.enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
    ChoixStatutParcoursDoctoral,
)
from parcours_doctoral.ddd.epreuve_confirmation.domain.service.epreuve_confirmation import EpreuveConfirmationService
from parcours_doctoral.ddd.formation.domain.model.enums import CategorieActivite, StatutActivite
from parcours_doctoral.models import (
    Activity,
    ActorType,
    ConfirmationPaper,
    ParcoursDoctoral,
    ParcoursDoctoralSupervisionActor,
)
from parcours_doctoral.models.private_defense import PrivateDefense
from parcours_doctoral.views.config.import_from_xlsx import (
    ChoixOuiNon,
    ForeignKey,
    UniqueIdValidationCondition,
    ValidationCondition,
    WorksheetConfig,
    ImportFromXLSXView,
)
from reference.models.country import Country

__all__ = [
    'DoctorateImportFromXLSXView',
]

MAPPING_COMMISSION_PROXIMITE: dict[str, str] = {
    'ECONOMY': ChoixCommissionProximiteCDEouCLSM.ECONOMY.name,
    'MANAGEMENT': ChoixCommissionProximiteCDEouCLSM.MANAGEMENT.name,
    'ECLI': ChoixCommissionProximiteCDSS.ECLI.name,
    'BCGIM': ChoixCommissionProximiteCDSS.BCGIM.name,
    'NRSC': ChoixCommissionProximiteCDSS.NRSC.name,
    'SPSS': ChoixCommissionProximiteCDSS.SPSS.name,
    'DENT': ChoixCommissionProximiteCDSS.DENT.name,
    'DFAR': ChoixCommissionProximiteCDSS.DFAR.name,
    'MOTR': ChoixCommissionProximiteCDSS.MOTR.name,
    'PHYSICS': ChoixSousDomaineSciences.PHYSICS.name,
    'CHEMISTRY': ChoixSousDomaineSciences.CHEMISTRY.name,
    'MATHEMATICS': ChoixSousDomaineSciences.MATHEMATICS.name,
    'STATISTICS': ChoixSousDomaineSciences.STATISTICS.name,
    'BIOLOGY': ChoixSousDomaineSciences.BIOLOGY.name,
    'GEOGRAPHY': ChoixSousDomaineSciences.GEOGRAPHY.name,
}

MAPPING_STATUT = {
    'ADMIS': ChoixStatutParcoursDoctoral.ADMIS.name,
    'EN_ATTENTE_DE_SIGNATURE': ChoixStatutParcoursDoctoral.EN_ATTENTE_DE_SIGNATURE.name,
    'CONFIRMATION_SOUMISE': ChoixStatutParcoursDoctoral.CONFIRMATION_SOUMISE.name,
    'CONFIRMATION_REUSSIE': ChoixStatutParcoursDoctoral.CONFIRMATION_REUSSIE.name,
    'CONFIRMATION_A_REPRESENTER': ChoixStatutParcoursDoctoral.CONFIRMATION_A_REPRESENTER.name,
    'NON_AUTORISE_A_POURSUIVRE': ChoixStatutParcoursDoctoral.NON_AUTORISE_A_POURSUIVRE.name,
}

MAPPING_TYPE_ACTEUR = {
    'PROMOTER': ActorType.PROMOTER.name,
    'CA_MEMBER': ActorType.CA_MEMBER.name,
}

MAPPING_CHAMP_CATEGORIE_ACTIVITE = {
    'formation_doctorale_colloques_conferences_ects': CategorieActivite.CONFERENCE.name,
    'formation_doctorale_communications_orales_hors_conf_ects': CategorieActivite.COMMUNICATION.name,
    'formation_doctorale_seminaires_suivis_ects': CategorieActivite.SEMINAR.name,
    'formation_doctorale_publications_ects': CategorieActivite.PUBLICATION.name,
    'formation_doctorale_services_ects': CategorieActivite.SERVICE.name,
    'formation_doctorale_sejours_recherche_ects': CategorieActivite.RESIDENCY.name,
    'formation_doctorale_vae_ects': CategorieActivite.VAE.name,
    'formation_doctorale_cours_formations_ecoles_ects': CategorieActivite.COURSE.name,
    'formation_doctorale_epreuves_ects': CategorieActivite.PAPER.name,
}

ECTS_FIELD = Field(max_digits=3, decimal_places=1, default=0, ge=0)


class DoctorateImportModel(BaseModel):
    identification_noma: ForeignKey = Field(pattern=r'^\d{8}$')
    identification_nom_etudiant: str
    choix_formation_secteur: str
    choix_formation_sigle_doctorat: ForeignKey
    choix_formation_commission_proximite: Optional[Literal[*MAPPING_COMMISSION_PROXIMITE]]
    choix_formation_date_admission: date
    projet_recherche_duree_prevue_realisation_doctorat: Optional[int] = Field(ge=0, le=200)
    projet_recherche_temps_consacre_these: Optional[int] = Field(ge=0, le=100)
    projet_recherche_sujet: str = Field(max_length=1023)
    projet_recherche_sigle_institut_recherche: ForeignKey
    projet_recherche_lieu_these: str = Field(max_length=255)
    cotutelle_cotutelle: ChoixOuiNon
    cotutelle_institution_fwb: Optional[ChoixOuiNon]
    cotutelle_nom_etablissement: Optional[str] = Field(max_length=255)
    formation_doctorale_colloques_conferences_ects: decimal.Decimal = ECTS_FIELD
    formation_doctorale_communications_orales_hors_conf_ects: decimal.Decimal = ECTS_FIELD
    formation_doctorale_seminaires_suivis_ects: decimal.Decimal = ECTS_FIELD
    formation_doctorale_publications_ects: decimal.Decimal = ECTS_FIELD
    formation_doctorale_services_ects: decimal.Decimal = ECTS_FIELD
    formation_doctorale_sejours_recherche_ects: decimal.Decimal = ECTS_FIELD
    formation_doctorale_vae_ects: decimal.Decimal = ECTS_FIELD
    formation_doctorale_cours_formations_ecoles_ects: decimal.Decimal = ECTS_FIELD
    formation_doctorale_epreuves_ects: decimal.Decimal = ECTS_FIELD
    epreuve_confirmation_date_limite: Optional[date]
    epreuve_confirmation_date_epreuve: Optional[date]
    epreuve_confirmation_statut: Literal[*MAPPING_STATUT]

    @field_validator('cotutelle_institution_fwb', 'cotutelle_nom_etablissement')
    @classmethod
    def validate_cotutelle_fields(cls, input_value: Any, info: ValidationInfo):
        if info.data.get('cotutelle_cotutelle') == ChoixOuiNon.OUI and not input_value:
            raise PydanticCustomError(
                'cotutelle_data_error',
                'The field is required with thesis under joint supervision',
            )
        return input_value

    @field_validator('choix_formation_sigle_doctorat')
    @classmethod
    def has_valid_enrolment(cls, input_value: Any, info: ValidationInfo):
        if (info.data.get('identification_noma'), input_value) not in info.context['db_data'][
            ('identification_noma', 'choix_formation_sigle_doctorat')
        ]:
            raise PydanticCustomError(
                'invalid_enrolment',
                'No enrolment has been found for this student for this training',
            )
        return input_value


class SupervisionImportModel(BaseModel):
    noma_doctorant: ForeignKey = Field(pattern=r'^\d{8}$')
    promoteur_ou_membre: Literal[*MAPPING_TYPE_ACTEUR]
    est_promoteur_reference: ChoixOuiNon
    prenom: str = Field(max_length=50)
    nom: str = Field(max_length=50)
    email: str = Field(max_length=255)
    doctorat_avec_these: Optional[ChoixOuiNon]
    institution: Optional[str] = Field(max_length=255)
    ville: Optional[str] = Field(max_length=255)
    pays: Optional[ForeignKey]
    langue_contact: Optional[Literal[tuple(x[0] for x in settings.LANGUAGES)]]

    @field_validator('doctorat_avec_these', 'institution', 'ville', 'pays', 'langue_contact')
    @classmethod
    def validate_external_fields(cls, input_value: Any, info: ValidationInfo):
        if info.data.get('email') not in info.context['db_data']['email'] and not input_value:
            raise PydanticCustomError(
                'external_promoter_data_error',
                'The field is required for an external member',
            )
        return input_value

    @field_validator('est_promoteur_reference')
    @classmethod
    def is_lead_promoter(cls, input_value: Any, info: ValidationInfo):
        if info.data.get('promoteur_ou_membre') == 'CA_MEMBER' and input_value == ChoixOuiNon.OUI:
            raise PydanticCustomError(
                'promoter_data_error',
                'The field can only be true for a promoter',
            )
        return input_value


class DoctorateImportFromXLSXView(ImportFromXLSXView):
    urlpatterns = 'doctorate-import-from-xlsx'
    template_name = 'parcours_doctoral/config/excel_import.html'
    import_title = gettext_lazy('Doctorate import')

    def __init__(self, *args, **kwargs):
        doctorate_worksheet_config: WorksheetConfig[DoctorateImportModel] = WorksheetConfig(
            validation_model_class=DoctorateImportModel,
            with_header=True,
            additional_validations_conditions=[
                UniqueIdValidationCondition('identification_noma'),
            ],
        )

        supervision_worksheet_config: WorksheetConfig[SupervisionImportModel] = WorksheetConfig(
            validation_model_class=SupervisionImportModel,
            with_header=True,
            additional_validations_conditions=[
                UniqueIdValidationCondition('noma_doctorant', 'email'),
                ValidationCondition(
                    validation_method=lambda row: row['est_promoteur_reference'] == ChoixOuiNon.OUI.value,
                    no_valid_row_message='One contact supervisor must be selected for each doctorate.',
                    valid_rows_max_number=1,
                    too_much_valid_rows_message='There is too much contact supervisors for this doctorate.',
                    validation_key_fields=('noma_doctorant',),
                ),
            ],
        )

        super().__init__(
            worksheet_configs=(doctorate_worksheet_config, supervision_worksheet_config),
            *args,
            **kwargs,
        )

    def load_worksheet_validation_context_data(self):
        doctorate_worksheet_config: WorksheetConfig[DoctorateImportModel] = self.worksheet_configs[0]
        supervision_worksheet_config: WorksheetConfig[SupervisionImportModel] = self.worksheet_configs[1]

        db_doctorate_data_ids = doctorate_worksheet_config.get_sets_of_data_by_col(
            'identification_noma',
            'choix_formation_sigle_doctorat',
            'projet_recherche_sigle_institut_recherche',
            ('identification_noma', 'choix_formation_sigle_doctorat'),
        )

        enrolments = (
            InscriptionProgrammeAnnuel.objects.filter(
                programme__offer__education_group_type__name=TrainingType.PHD.name,
                programme__offer__academic_year__year=F('programme_cycle__annee_formation'),
            )
            .alias(
                acronym_noma=Tuple('programme_cycle__etudiant__registration_id', 'programme__offer__acronym'),
            )
            .filter(
                acronym_noma__in=db_doctorate_data_ids[('identification_noma', 'choix_formation_sigle_doctorat')],
            )
            .annotate(
                registration_id=F('programme_cycle__etudiant__registration_id'),
                offer_acronym=F('programme__offer__acronym'),
                offer_id=F('programme__offer_id'),
            )
            .only('pk')
        )

        training_id_by_noma_and_acronym: dict[tuple[str, str], int] = {
            (enrolment.registration_id, enrolment.offer_acronym): enrolment.offer_id for enrolment in enrolments
        }

        students = Student.objects.filter(registration_id__in=db_doctorate_data_ids['identification_noma']).only(
            'registration_id',
            'person_id',
        )

        trainings = EducationGroupYear.objects.filter(
            acronym__in=db_doctorate_data_ids['choix_formation_sigle_doctorat']
        ).only('acronym', 'id')

        entity_versions = EntityVersion.objects.filter(
            acronym__in=db_doctorate_data_ids['projet_recherche_sigle_institut_recherche']
        ).only('acronym', 'id')

        doctorate_worksheet_config.validation_context_data = {
            'identification_noma': {student.registration_id: student.person_id for student in students},
            'choix_formation_sigle_doctorat': {training.acronym: training.id for training in trainings},
            'projet_recherche_sigle_institut_recherche': {entity.acronym: entity.id for entity in entity_versions},
            ('identification_noma', 'choix_formation_sigle_doctorat'): training_id_by_noma_and_acronym,
        }

        db_supervision_data_ids = supervision_worksheet_config.get_sets_of_data_by_col(
            'email',
            'pays',
        )

        persons = (
            Person.objects.filter(
                # Keep only persons with internal account and email address
                global_id__startswith='0',
                email__endswith=settings.INTERNAL_EMAIL_SUFFIX,
                email__in=db_supervision_data_ids['email'],
            )
            .filter(
                # Remove students who aren't tutors
                ~Exists(Student.objects.filter(person=OuterRef('pk'), person__tutor__isnull=True)),
            )
            .only('email', 'id')
        )

        countries = Country.objects.filter(iso_code__in=db_supervision_data_ids['pays']).only('iso_code', 'id')

        supervision_worksheet_config.validation_context_data = {
            'email': {person.email: person.id for person in persons},
            'pays': {country.iso_code: country.id for country in countries},
            'noma_doctorant': doctorate_worksheet_config.validation_context_data['identification_noma'],
        }

    def save_worksheet_data(self):
        doctorate_worksheet_config: WorksheetConfig[DoctorateImportModel] = self.worksheet_configs[0]
        supervision_worksheet_config: WorksheetConfig[SupervisionImportModel] = self.worksheet_configs[1]

        activities: list[Activity] = []
        confirmation_papers: list[ConfirmationPaper] = []
        doctorates: list[ParcoursDoctoral] = []
        private_defenses: list[PrivateDefense] = []
        supervision_processes_by_key: dict[str, Process] = {}

        for validated_object in doctorate_worksheet_config.validated_objects:
            key = validated_object.identification_noma

            supervision_processes_by_key[key] = Process()
            doctorate = ParcoursDoctoral(
                supervision_group=supervision_processes_by_key[validated_object.identification_noma],
                admission_type=ChoixTypeAdmission.ADMISSION.name,
                student_id=doctorate_worksheet_config.validation_context_data['identification_noma'][
                    validated_object.identification_noma
                ],
                training_id=doctorate_worksheet_config.validation_context_data[
                    ('identification_noma', 'choix_formation_sigle_doctorat')
                ][
                    (
                        validated_object.identification_noma,
                        validated_object.choix_formation_sigle_doctorat,
                    )
                ],
                admission_approved_by_cdd_at=validated_object.choix_formation_date_admission,
                planned_duration=validated_object.projet_recherche_duree_prevue_realisation_doctorat,
                dedicated_time=validated_object.projet_recherche_temps_consacre_these,
                project_title=validated_object.projet_recherche_sujet,
                thesis_institute_id=doctorate_worksheet_config.validation_context_data[
                    'projet_recherche_sigle_institut_recherche'
                ][validated_object.projet_recherche_sigle_institut_recherche],
                thesis_location=validated_object.projet_recherche_lieu_these,
                cotutelle=validated_object.cotutelle_cotutelle == ChoixOuiNon.OUI,
                cotutelle_institution_fwb=validated_object.cotutelle_institution_fwb == ChoixOuiNon.OUI,
                cotutelle_other_institution_name=validated_object.cotutelle_nom_etablissement,
                proximity_commission=MAPPING_COMMISSION_PROXIMITE.get(
                    validated_object.choix_formation_commission_proximite,
                    '',
                ),
                status=MAPPING_STATUT.get(
                    validated_object.epreuve_confirmation_statut,
                    ChoixStatutParcoursDoctoral.ADMIS.name,
                ),
            )

            doctorates.append(doctorate)

            for field, category in MAPPING_CHAMP_CATEGORIE_ACTIVITE.items():
                activity_ects = getattr(validated_object, field)
                if activity_ects:
                    activity = Activity(
                        parcours_doctoral=doctorate,
                        ects=activity_ects,
                        category=category,
                        status=StatutActivite.ACCEPTEE.name,
                    )
                    activities.append(activity)

            confirmation_papers.append(
                ConfirmationPaper(
                    parcours_doctoral=doctorate,
                    confirmation_date=validated_object.epreuve_confirmation_date_epreuve,
                    confirmation_deadline=validated_object.epreuve_confirmation_date_limite
                    if validated_object.epreuve_confirmation_date_limite
                    else (
                        validated_object.choix_formation_date_admission
                        + relativedelta(months=EpreuveConfirmationService.NB_MOIS_INTERVALLE_DATE_LIMITE)
                    )
                    if validated_object.choix_formation_date_admission
                    else None,
                )
            )

            private_defenses.append(
                PrivateDefense(
                    parcours_doctoral=doctorate,
                    current_parcours_doctoral=doctorate,
                )
            )

        Process.objects.bulk_create(objs=supervision_processes_by_key.values())
        ParcoursDoctoral.objects.bulk_create(objs=doctorates)
        ConfirmationPaper.objects.bulk_create(objs=confirmation_papers)
        PrivateDefense.objects.bulk_create(objs=private_defenses)
        Activity.objects.bulk_create(objs=activities)

        promoter_roles: list[Promoter] = []
        committee_member_roles: list[CommitteeMember] = []
        actors: list[ParcoursDoctoralSupervisionActor] = []
        states: list[StateHistory] = []

        for validated_object in supervision_worksheet_config.validated_objects:
            actor = ParcoursDoctoralSupervisionActor(
                process=supervision_processes_by_key[validated_object.noma_doctorant],
                type=MAPPING_TYPE_ACTEUR[validated_object.promoteur_ou_membre],
                is_reference_promoter=validated_object.est_promoteur_reference == ChoixOuiNon.OUI,
            )

            related_person_id = supervision_worksheet_config.validation_context_data['email'].get(
                validated_object.email
            )

            if related_person_id:
                # Internal member
                actor.person_id = related_person_id
                # We disable the proxy because the bulk_create method iterates over the foreign keys
                # and get the data of the related person
                actor._disable_proxy = True

                if actor.type == ActorType.PROMOTER.name:
                    promoter_roles.append(Promoter(person_id=related_person_id))

                if actor.type == ActorType.CA_MEMBER.name:
                    committee_member_roles.append(CommitteeMember(person_id=related_person_id))
            else:
                # External member
                actor.first_name = validated_object.prenom
                actor.last_name = validated_object.nom
                actor.email = validated_object.email
                actor.is_doctor = validated_object.doctorat_avec_these == ChoixOuiNon.OUI
                actor.institute = validated_object.institution
                actor.city = validated_object.ville
                actor.country_id = supervision_worksheet_config.validation_context_data['pays'][validated_object.pays]
                actor.language = validated_object.langue_contact

            states.append(
                StateHistory(
                    actor=actor,
                    state=SignatureState.APPROVED.name,
                )
            )
            actors.append(actor)

        ParcoursDoctoralSupervisionActor.objects.bulk_create(actors)
        StateHistory.objects.bulk_create(states)
        Promoter.objects.bulk_create(promoter_roles, ignore_conflicts=True)
        CommitteeMember.objects.bulk_create(committee_member_roles, ignore_conflicts=True)
