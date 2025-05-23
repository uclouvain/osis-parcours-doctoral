# Generated by Django 4.2.16 on 2025-03-19 16:15

from django.db import migrations, models

from parcours_doctoral.ddd.domain.model.enums import ChoixStatutParcoursDoctoral


def update_doctorate_status(apps, schema_editor):
    ParcoursDoctoral = apps.get_model("parcours_doctoral.ParcoursDoctoral")

    ParcoursDoctoral.objects.filter(
        status__in=[
            'EN_ATTENTE_INJECTION_EPC',
            'EN_COURS_DE_CREATION_PAR_GESTIONNAIRE',
        ]
    ).update(status=ChoixStatutParcoursDoctoral.ADMIS.name)


class Migration(migrations.Migration):

    dependencies = [
        ("parcours_doctoral", "0014_alter_activity_context"),
    ]

    operations = [
        migrations.AlterField(
            model_name="parcoursdoctoral",
            name="status",
            field=models.CharField(
                choices=[
                    ("ADMIS", "ADMIS"),
                    ("EN_ATTENTE_DE_SIGNATURE", "EN_ATTENTE_DE_SIGNATURE"),
                    ("CONFIRMATION_SOUMISE", "CONFIRMATION_SOUMISE"),
                    ("CONFIRMATION_REUSSIE", "CONFIRMATION_REUSSIE"),
                    ("NON_AUTORISE_A_POURSUIVRE", "NON_AUTORISE_A_POURSUIVRE"),
                    ("CONFIRMATION_A_REPRESENTER", "CONFIRMATION_A_REPRESENTER"),
                    ("JURY_SOUMIS", "JURY_SOUMIS"),
                    ("JURY_APPROUVE_CA", "JURY_APPROUVE_CA"),
                    ("JURY_APPROUVE_CDD", "JURY_APPROUVE_CDD"),
                    ("JURY_REFUSE_CDD", "JURY_REFUSE_CDD"),
                    ("JURY_APPROUVE_ADRE", "JURY_APPROUVE_ADRE"),
                    ("JURY_REFUSE_ADRE", "JURY_REFUSE_ADRE"),
                    ("ABANDON", "ABANDON"),
                ],
                default="ADMIS",
                max_length=64,
                verbose_name="Status",
            ),
        ),
        migrations.RunPython(code=update_doctorate_status, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name="parcoursdoctoral",
            name="cotutelle",
            field=models.BooleanField(blank=True, null=True),
        ),
    ]
