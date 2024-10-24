from admission.contrib.models import DoctorateAdmission
from admission.mail_templates import ADMISSION_EMAIL_GENERIC_ONCE_ADMITTED
from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral
from parcours_doctoral.mail_templates.confirmation_paper import ADMISSION_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT


def get_mail_templates_from_admission(admission: DoctorateAdmission):
    allowed_templates = []
    if admission.post_enrolment_status != ChoixStatutParcoursDoctoral.ADMISSION_IN_PROGRESS.name:
        allowed_templates.append(ADMISSION_EMAIL_GENERIC_ONCE_ADMITTED)
        if admission.post_enrolment_status == ChoixStatutParcoursDoctoral.SUBMITTED_CONFIRMATION.name:
            allowed_templates.append(ADMISSION_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT)
    return allowed_templates
