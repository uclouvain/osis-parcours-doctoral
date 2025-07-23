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
from collections import defaultdict
from typing import List, Optional, Union

from django.db.models import F, Prefetch
from django.db.models.functions import Coalesce
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from osis_signature.models import Actor, Process, StateHistory

from base.models.person import Person
from parcours_doctoral.auth.roles.ca_member import CommitteeMember
from parcours_doctoral.auth.roles.promoter import Promoter
from parcours_doctoral.ddd.builder.parcours_doctoral_identity import (
    ParcoursDoctoralIdentityBuilder,
)
from parcours_doctoral.ddd.domain.model._membre_CA import MembreCAIdentity
from parcours_doctoral.ddd.domain.model._promoteur import PromoteurIdentity
from parcours_doctoral.ddd.domain.model._signature_membre_CA import SignatureMembreCA
from parcours_doctoral.ddd.domain.model._signature_promoteur import SignaturePromoteur
from parcours_doctoral.ddd.domain.model.enums import ChoixEtatSignature
from parcours_doctoral.ddd.domain.model.groupe_de_supervision import (
    GroupeDeSupervision,
    GroupeDeSupervisionIdentity,
    SignataireIdentity,
)
from parcours_doctoral.ddd.dtos import MembreCADTO, PromoteurDTO
from parcours_doctoral.ddd.jury.domain.model.enums import RoleJury
from parcours_doctoral.ddd.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from parcours_doctoral.models import (
    ActorType,
    ParcoursDoctoral,
    ParcoursDoctoralSupervisionActor, JuryActor,
)
from reference.models.country import Country


class GroupeDeSupervisionRepository(IGroupeDeSupervisionRepository):
    @classmethod
    def _get_queryset(cls):
        return (
            ParcoursDoctoral.objects.select_related('supervision_group')
            .only(
                "uuid",
                "status",
                "supervision_group",
            )
            .prefetch_related(
                Prefetch(
                    'supervision_group__actors',
                    Actor.objects.alias(dynamic_last_name=Coalesce(F('last_name'), F('person__last_name')))
                    .select_related('parcoursdoctoralsupervisionactor')
                    .order_by('dynamic_last_name'),
                    to_attr='ordered_members',
                )
            )
        )

    @classmethod
    def _load(cls, parcours_doctoral):
        if not parcours_doctoral.supervision_group_id:
            parcours_doctoral.supervision_group = Process.objects.create()
            parcours_doctoral.save(update_fields=['supervision_group'])

        groupe = parcours_doctoral.supervision_group
        actors = defaultdict(list)
        for actor in getattr(groupe, 'ordered_members', []):
            actors[actor.parcoursdoctoralsupervisionactor.type].append(actor)

        return GroupeDeSupervision(
            entity_id=GroupeDeSupervisionIdentity(uuid=groupe.uuid),
            parcours_doctoral_id=ParcoursDoctoralIdentityBuilder.build_from_uuid(parcours_doctoral.uuid),
            signatures_promoteurs=[
                SignaturePromoteur(
                    promoteur_id=PromoteurIdentity(str(actor.uuid)),
                    etat=ChoixEtatSignature[actor.state],
                    date=actor.last_state_date,
                    commentaire_externe=actor.comment,
                    commentaire_interne=actor.parcoursdoctoralsupervisionactor.internal_comment,
                    pdf=actor.parcoursdoctoralsupervisionactor.pdf_from_candidate,
                )
                for actor in actors.get(ActorType.PROMOTER.name, [])
            ],
            signatures_membres_CA=[
                SignatureMembreCA(
                    membre_CA_id=MembreCAIdentity(str(actor.uuid)),
                    etat=ChoixEtatSignature[actor.state],
                    date=actor.last_state_date,
                    commentaire_externe=actor.comment,
                    commentaire_interne=actor.parcoursdoctoralsupervisionactor.internal_comment,
                    pdf=actor.parcoursdoctoralsupervisionactor.pdf_from_candidate,
                )
                for actor in actors.get(ActorType.CA_MEMBER.name, [])
            ],
            promoteur_reference_id=next(
                (
                    PromoteurIdentity(actor.uuid)
                    for actor in actors.get(ActorType.PROMOTER.name, [])
                    if actor.parcoursdoctoralsupervisionactor.is_reference_promoter
                ),
                None,
            ),
            statut_signature=None,
            # FIXME
            # statut_signature=ChoixStatutSignatureGroupeDeSupervision.SIGNING_IN_PROGRESS
            # if parcours_doctoral.status == ChoixStatutParcoursDoctoral.EN_ATTENTE_DE_SIGNATURE.name
            # else None,
        )

    @classmethod
    def get_by_parcours_doctoral_id(cls, parcours_doctoral_id: 'ParcoursDoctoralIdentity') -> 'GroupeDeSupervision':
        parcours_doctoral = cls._get_queryset().get(uuid=parcours_doctoral_id.uuid)
        return cls._load(parcours_doctoral)

    @classmethod
    def get(cls, entity_id: 'GroupeDeSupervisionIdentity') -> 'GroupeDeSupervision':
        raise NotImplementedError

    @classmethod
    def search(
        cls,
        entity_ids: Optional[List['GroupeDeSupervisionIdentity']] = None,
        matricule_membre: str = None,
        **kwargs,
    ) -> List['GroupeDeSupervision']:
        if matricule_membre:
            parcours_doctorals = (
                cls._get_queryset()
                .filter(supervision_group__actors__person__global_id=matricule_membre)
                .distinct('pk')
                .order_by('-pk')
            )
            return [cls._load(parcours_doctoral) for parcours_doctoral in parcours_doctorals]
        raise NotImplementedError

    @classmethod
    def delete(cls, entity_id: 'GroupeDeSupervisionIdentity', **kwargs) -> None:
        raise NotImplementedError

    @classmethod
    def save(cls, entity: 'GroupeDeSupervision') -> None:
        parcours_doctoral = (
            ParcoursDoctoral.objects.select_related('supervision_group')
            .only('supervision_group')
            .get(uuid=entity.parcours_doctoral_id.uuid)
        )
        if not parcours_doctoral.supervision_group_id:
            parcours_doctoral.supervision_group = groupe = Process.objects.create()
            parcours_doctoral.save(update_fields=['supervision_group'])
        else:
            groupe = parcours_doctoral.supervision_group

        current_promoteurs = groupe.actors.filter(parcoursdoctoralsupervisionactor__type=ActorType.PROMOTER.name)
        current_members = groupe.actors.filter(parcoursdoctoralsupervisionactor__type=ActorType.CA_MEMBER.name)

        # Remove old CA members (deleted by refusal)
        current_members.exclude(uuid__in=[s.membre_CA_id.uuid for s in entity.signatures_membres_CA]).delete()

        # Update existing actors
        cls._update_members(current_promoteurs, entity.signatures_promoteurs, entity.promoteur_reference_id)
        cls._update_members(current_members, entity.signatures_membres_CA)

    @classmethod
    def _update_members(
        cls,
        member_list: list,
        signature_list: Union[List[SignaturePromoteur], List[SignatureMembreCA]],
        reference_promoter: Optional[PromoteurIdentity] = None,
    ):
        for actor in member_list:
            membre = cls._get_member(signature_list, str(actor.uuid))
            if actor.state != membre.etat.name:
                StateHistory.objects.create(state=membre.etat.name, actor_id=actor.id)
                if membre.etat.name in [ChoixEtatSignature.APPROVED.name, ChoixEtatSignature.DECLINED.name]:
                    actor.comment = membre.commentaire_externe
                    actor.parcoursdoctoralsupervisionactor.pdf_from_candidate = membre.pdf
                    actor.parcoursdoctoralsupervisionactor.internal_comment = membre.commentaire_interne
                    actor.parcoursdoctoralsupervisionactor.rejection_reason = membre.motif_refus
                    actor.parcoursdoctoralsupervisionactor.is_reference_promoter = bool(
                        reference_promoter and str(actor.uuid) == str(reference_promoter.uuid)
                    )
                    actor.parcoursdoctoralsupervisionactor.save()
                    actor.save()
            if (
                # Actor is no longer the reference promoter
                actor.parcoursdoctoralsupervisionactor.is_reference_promoter
                and (not reference_promoter or str(actor.uuid) != str(reference_promoter.uuid))
            ):
                actor.parcoursdoctoralsupervisionactor.is_reference_promoter = False
                actor.parcoursdoctoralsupervisionactor.save()
            elif (
                # Actor is the reference promoter and need to be updated
                reference_promoter
                and not actor.parcoursdoctoralsupervisionactor.is_reference_promoter
                and str(actor.uuid) == str(reference_promoter.uuid)
            ):
                actor.parcoursdoctoralsupervisionactor.is_reference_promoter = True
                actor.parcoursdoctoralsupervisionactor.save()

    @classmethod
    def _get_member(cls, signatures: list, uuid: str) -> Union[SignaturePromoteur, SignatureMembreCA]:
        if isinstance(signatures[0], SignaturePromoteur):
            return next(s for s in signatures if s.promoteur_id.uuid == uuid)  # pragma: no branch
        return next(s for s in signatures if s.membre_CA_id.uuid == uuid)  # pragma: no branch

    @classmethod
    def add_member(
        cls,
        groupe_id: 'GroupeDeSupervisionIdentity',
        type: Optional[ActorType] = None,
        matricule: Optional[str] = '',
        first_name: Optional[str] = '',
        last_name: Optional[str] = '',
        email: Optional[str] = '',
        is_doctor: bool = False,
        institute: Optional[str] = '',
        city: Optional[str] = '',
        country_code: Optional[str] = '',
        language: Optional[str] = '',
    ) -> 'SignataireIdentity':
        groupe = Process.objects.get(uuid=groupe_id.uuid)
        person = Person.objects.get(global_id=matricule) if matricule else None
        new_actor = ParcoursDoctoralSupervisionActor.objects.create(
            process=groupe,
            person=person,
            type=type.name,
            first_name=first_name,
            last_name=last_name,
            email=email,
            is_doctor=is_doctor,
            institute=institute,
            city=city,
            country=Country.objects.get(iso_code=country_code) if country_code else None,
            language=language,
        )
        if type == ActorType.PROMOTER:
            group_name, model = 'promoters', Promoter
            signataire_id = PromoteurIdentity(str(new_actor.uuid))
            JuryActor.objects.create(
                role=RoleJury.MEMBRE.name,
                process_id=ParcoursDoctoral.objects.only('id', 'jury_group_id').get(supervision_group=groupe).jury_group_id,
                is_promoter=True,
                **(
                    {'person_id': new_actor.person_id}
                    if new_actor.person_id
                    else {
                        'first_name': new_actor.first_name,
                        'last_name': new_actor.last_name,
                        'email': new_actor.email,
                        'institute': new_actor.institute,
                        'city': new_actor.city,
                        'country_id': new_actor.country_id,
                        'language': new_actor.language,
                    }
                ),
            )
        else:
            group_name, model = 'committee_members', CommitteeMember
            signataire_id = MembreCAIdentity(str(new_actor.uuid))
        # Make sure the person has relevant role
        if person:
            model.objects.update_or_create(person=person)
        return signataire_id

    @classmethod
    def remove_member(cls, groupe_id: 'GroupeDeSupervisionIdentity', signataire: 'SignataireIdentity') -> None:
        member = (
            ParcoursDoctoralSupervisionActor.objects.only('id', 'type')
            .select_related(None)
            .get(
                process__uuid=groupe_id.uuid,
                uuid=signataire.uuid,
            )
        )
        if member.type == ActorType.PROMOTER.name:
            JuryMember.objects.filter(promoter_id=member.id).delete()
        member.delete()

    @classmethod
    def get_members(cls, groupe_id: 'GroupeDeSupervisionIdentity') -> List[Union['PromoteurDTO', 'MembreCADTO']]:
        actors = ParcoursDoctoralSupervisionActor.objects.select_related('person__tutor').filter(
            process__uuid=groupe_id.uuid,
        )
        members = []
        for actor in actors:
            klass = PromoteurDTO if actor.type == ActorType.PROMOTER.name else MembreCADTO
            members.append(
                klass(
                    uuid=actor.uuid,
                    matricule=actor.person and actor.person.global_id,
                    nom=actor.last_name,
                    prenom=actor.first_name,
                    email=actor.email,
                    est_docteur=True if not actor.is_external and hasattr(actor.person, 'tutor') else actor.is_doctor,
                    institution=_('ucl') if not actor.is_external else actor.institute,
                    ville=actor.city,
                    pays=actor.country_id
                    and getattr(actor.country, 'name_en' if get_language() == 'en' else 'name')
                    or '',
                    est_externe=actor.is_external,
                )
            )
        return members

    @classmethod
    def edit_external_member(
        cls,
        groupe_id: 'GroupeDeSupervisionIdentity',
        membre_id: 'SignataireIdentity',
        first_name: Optional[str] = '',
        last_name: Optional[str] = '',
        email: Optional[str] = '',
        is_doctor: Optional[bool] = False,
        institute: Optional[str] = '',
        city: Optional[str] = '',
        country_code: Optional[str] = '',
        language: Optional[str] = '',
    ) -> None:
        ParcoursDoctoralSupervisionActor.objects.filter(process__uuid=groupe_id.uuid, uuid=membre_id.uuid).update(
            first_name=first_name,
            last_name=last_name,
            email=email,
            is_doctor=is_doctor,
            institute=institute,
            city=city,
            country=Country.objects.get(iso_code=country_code) if country_code else None,
            language=language,
        )
