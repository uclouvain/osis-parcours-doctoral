from django.core import cache
from django.shortcuts import get_object_or_404

from admission.models import DoctorateAdmission
from admission.mail_templates import ADMISSION_EMAIL_GENERIC_ONCE_ADMITTED
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.mail_templates.confirmation_paper import ADMISSION_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT
from parcours_doctoral.models.parcours_doctoral import ParcoursDoctoral


def get_mail_templates_from_admission(admission: DoctorateAdmission):
    allowed_templates = []
    if admission.post_enrolment_status != ChoixStatutParcoursDoctoral.ADMISSION_IN_PROGRESS.name:
        allowed_templates.append(ADMISSION_EMAIL_GENERIC_ONCE_ADMITTED)
        if admission.post_enrolment_status == ChoixStatutParcoursDoctoral.SUBMITTED_CONFIRMATION.name:
            allowed_templates.append(ADMISSION_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT)
    return allowed_templates


def get_cached_parcours_doctoral_perm_obj(parcours_doctoral_uuid):
    qs = ParcoursDoctoral.objects.select_related(
        'candidate',
        'training__academic_year',
    )
    return cache.get_or_set(
        'parcours_doctoral_permission_{}'.format(parcours_doctoral_uuid),
        lambda: get_object_or_404(qs, uuid=parcours_doctoral_uuid),
    )
