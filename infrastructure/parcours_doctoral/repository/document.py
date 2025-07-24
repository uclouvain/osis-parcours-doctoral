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
from typing import Dict, List

from django.db.models import Prefetch
from django.utils.dateparse import parse_datetime
from osis_document.enums import PostProcessingWanted

from base.models.person import Person
from parcours_doctoral.ddd.domain.model.document import (
    Document,
    DocumentIdentity,
    TypeDocument,
)
from parcours_doctoral.ddd.domain.model.enums import ChoixEtapeParcoursDoctoral
from parcours_doctoral.ddd.domain.model.parcours_doctoral import (
    ParcoursDoctoralIdentity,
)
from parcours_doctoral.ddd.domain.validator.exceptions import (
    DocumentNonTrouveException,
    ParcoursDoctoralNonTrouveException,
    PersonneNonTrouveeException,
)
from parcours_doctoral.ddd.dtos.document import AuteurDocumentDTO, DocumentDTO
from parcours_doctoral.ddd.repository.i_document import IDocumentRepository
from parcours_doctoral.models import ConfirmationPaper
from parcours_doctoral.models import Document as DocumentDbModel
from parcours_doctoral.models import ParcoursDoctoral


class DocumentRepository(IDocumentRepository):
    @classmethod
    def _get_document_object(cls, entity_id: DocumentIdentity) -> DocumentDbModel:
        try:
            return DocumentDbModel.objects.select_related('updated_by').get(uuid=entity_id.identifiant)
        except DocumentDbModel.DoesNotExist:
            raise DocumentNonTrouveException

    @classmethod
    def get(cls, entity_id: DocumentIdentity) -> Document:
        document_db_obj = cls._get_document_object(entity_id=entity_id)

        return Document(
            entity_id=entity_id,
            uuids_documents=document_db_obj.file,
            type=TypeDocument[document_db_obj.document_type],
            libelle=document_db_obj.name,
            modifie_le=document_db_obj.updated_at,
            auteur=document_db_obj.updated_by.global_id if document_db_obj.updated_by else '',
        )

    @classmethod
    def get_dto(cls, entity_id: DocumentIdentity) -> DocumentDTO:
        document_db_obj = cls._get_document_object(entity_id=entity_id)
        return cls._get_dto_from_db_object(document_db_obj)

    @classmethod
    def recuperer_metadonnees_par_uuid_document(cls, uuids_documents: List[str]) -> Dict[str, Dict]:
        from osis_document.api.utils import (
            get_remote_tokens,
            get_several_remote_metadata,
        )

        tokens = get_remote_tokens(
            uuids_documents,
            wanted_post_process=PostProcessingWanted.ORIGINAL.name,
        )
        metadata = get_several_remote_metadata(list(tokens.values()))

        return {
            uuid: metadata[tokens[uuid]] if uuid in tokens and tokens[uuid] in metadata else {}
            for uuid in uuids_documents
        }

    @classmethod
    def recuperer_acteurs_dto_par_matricule(
        cls,
        metadonnees: dict,
    ) -> Dict[str, AuteurDocumentDTO]:
        matricules_acteurs = set()
        for donnees in metadonnees.values():
            matricules_acteurs.add(donnees.get('author'))

        if not matricules_acteurs:
            return {}

        return {
            person.global_id: AuteurDocumentDTO(
                matricule=person.global_id,
                nom=person.last_name,
                prenom=person.first_name,
            )
            for person in Person.objects.filter(global_id__in=matricules_acteurs).only(
                'global_id',
                'first_name',
                'last_name',
            )
        }

    confirmation_paper_fields_names = {
        field_name: ConfirmationPaper._meta.get_field(field_name).verbose_name
        for field_name in [
            'research_report',
            'supervisor_panel_report',
            'supervisor_panel_report_canvas',
            'research_mandate_renewal_opinion',
            'certificate_of_failure',
            'certificate_of_achievement',
            'justification_letter',
        ]
    }

    jury_fields_names = {
        field_name: ParcoursDoctoral._meta.get_field(field_name).verbose_name
        for field_name in [
            'jury_approval',
        ]
    }

    @classmethod
    def get_dtos_parcours_doctoral(
        cls,
        parcours_doctoral_id: ParcoursDoctoralIdentity,
    ) -> Dict[str, List[DocumentDTO]]:
        documents: Dict[str, List[DocumentDTO]] = {}

        doctorate = ParcoursDoctoral.objects.prefetch_related(
            Prefetch(
                'confirmationpaper_set',
                queryset=ConfirmationPaper.objects.order_by('created_at'),
            ),
            Prefetch(
                'document_set',
                queryset=DocumentDbModel.objects.select_related('updated_by').order_by('updated_at'),
            ),
        ).get(uuid=parcours_doctoral_id.uuid)

        cls._set_non_free_documents_dtos(doctorate, documents)

        # Set free and system documents
        documents[TypeDocument.LIBRE.value] = []
        documents[TypeDocument.SYSTEME.value] = []

        for document in doctorate.document_set.all():
            documents[TypeDocument[document.document_type].value].append(cls._get_dto_from_db_object(document))

        return documents

    @classmethod
    def _get_dto_from_db_object(cls, document: DocumentDbModel) -> DocumentDTO:
        return DocumentDTO(
            identifiant=str(document.uuid),
            uuids_documents=document.file,
            type=document.document_type,
            libelle=document.name,
            auteur=(
                AuteurDocumentDTO(
                    matricule=document.updated_by.global_id,
                    nom=document.updated_by.last_name,
                    prenom=document.updated_by.first_name,
                )
                if document.updated_by
                else None
            ),
            modifie_le=document.updated_at,
        )

    @classmethod
    def _set_non_free_documents_dtos(
        cls,
        doctorate: ParcoursDoctoral,
        documents: Dict[str, List[DocumentDTO]],
    ):
        # Add non-free documents
        documents_uuids: List[str] = []

        # Confirmation
        document_name_by_uuid = {}
        documents_categories_by_uuid = {}

        confirmation_papers = doctorate.confirmationpaper_set.all()
        confirmation_category_label = ChoixEtapeParcoursDoctoral.CONFIRMATION.value

        if len(confirmation_papers) > 1:
            confirmation_category_label += ' - {index}'

        for index, confirmation_paper in enumerate(confirmation_papers, start=1):
            document_category = confirmation_category_label.format(index=index)
            for field_name, field_verbose_name in cls.confirmation_paper_fields_names.items():
                field_value = getattr(confirmation_paper, field_name)

                for file_uuid in field_value:
                    file_uuid_as_str = str(file_uuid)
                    documents_uuids.append(file_uuid_as_str)
                    document_name_by_uuid[file_uuid_as_str] = field_verbose_name
                    documents_categories_by_uuid[file_uuid_as_str] = document_category

        # Jury
        for field_name, field_verbose_name in cls.jury_fields_names.items():
            field_value = getattr(doctorate, field_name)

            for file_uuid in field_value:
                file_uuid_as_str = str(file_uuid)
                documents_uuids.append(file_uuid_as_str)
                document_name_by_uuid[file_uuid_as_str] = field_verbose_name
                documents_categories_by_uuid[file_uuid_as_str] = ChoixEtapeParcoursDoctoral.JURY.value

        metadata = cls.recuperer_metadonnees_par_uuid_document(documents_uuids)

        actors = cls.recuperer_acteurs_dto_par_matricule(metadonnees=metadata)

        for document_uuid in documents_uuids:
            document_uuid_as_str = str(document_uuid)

            document_metadata = metadata.get(document_uuid_as_str, {})

            document_date = document_metadata.get('uploaded_at')
            document_author = document_metadata.get('author')

            document_category = documents_categories_by_uuid[document_uuid_as_str]

            if document_category not in documents:
                documents[document_category] = []

            documents[document_category].append(
                DocumentDTO(
                    identifiant=str(document_uuid),
                    uuids_documents=[document_uuid],
                    type=TypeDocument.NON_LIBRE.name,
                    libelle=document_name_by_uuid[document_uuid_as_str],
                    auteur=actors.get(document_author) if document_author else None,
                    modifie_le=parse_datetime(document_date) if document_date else None,
                )
            )

    @classmethod
    def save(cls, entity: Document) -> None:
        try:
            doctorate_id = ParcoursDoctoral.objects.only('pk').get(uuid=entity.entity_id.parcours_doctoral_id.uuid).pk
        except ParcoursDoctoral.DoesNotExist:
            raise ParcoursDoctoralNonTrouveException

        if entity.auteur:
            try:
                author_id = Person.objects.only('pk').get(global_id=entity.auteur).pk
            except Person.DoesNotExist:
                raise PersonneNonTrouveeException
        else:
            author_id = ''

        _, __ = DocumentDbModel.objects.update_or_create(
            uuid=entity.entity_id.identifiant,
            defaults={
                'name': entity.libelle,
                'updated_at': entity.modifie_le,
                'updated_by_id': author_id,
                'file': entity.uuids_documents,
                'related_doctorate_id': doctorate_id,
                'document_type': entity.type.name,
            },
        )

    @classmethod
    def delete(cls, entity_id: DocumentIdentity, **kwargs) -> None:
        nb_deleted, _ = DocumentDbModel.objects.filter(uuid=entity_id.identifiant).delete()

        if not nb_deleted:
            raise DocumentNonTrouveException
