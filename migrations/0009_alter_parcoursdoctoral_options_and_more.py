# Generated by Django 4.2.16 on 2024-11-20 15:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0707_django_4_migration"),
        ("parcours_doctoral", "0008_alter_parcoursdoctoral_options_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="parcoursdoctoral",
            options={
                "ordering": ("-created_at",),
                "permissions": [
                    ("download_jury_approved_pdf", "Can download jury-approved PDF"),
                    ("upload_jury_approved_pdf", "Can upload jury-approved PDF"),
                    ("validate_registration", "Can validate registration"),
                    ("approve_jury", "Can approve jury"),
                    ("approve_confirmation_paper", "Can approve confirmation paper"),
                    ("validate_doctoral_training", "Can validate doctoral training"),
                    (
                        "view_admission_jury",
                        "Can view the information related to the admission jury",
                    ),
                    (
                        "change_admission_jury",
                        "Can update the information related to the admission jury",
                    ),
                    (
                        "view_confirmation",
                        "Can view the information related to the confirmation paper",
                    ),
                    (
                        "change_admission_confirmation",
                        "Can update the information related to the confirmation paper",
                    ),
                ],
                "verbose_name": "Doctoral training",
            },
        ),
        migrations.AlterField(
            model_name="cddconfiguration",
            name="cdd",
            field=models.OneToOneField(
                limit_choices_to={"organization__type": "MAIN"},
                on_delete=django.db.models.deletion.CASCADE,
                related_name="admission_config",
                to="base.entity",
            ),
        ),
        migrations.AlterField(
            model_name="cddconfigurator",
            name="entity",
            field=models.ForeignKey(
                limit_choices_to={"organization__type": "MAIN"},
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="base.entity",
            ),
        ),
        migrations.AlterField(
            model_name="cddmailtemplate",
            name="cdd",
            field=models.ForeignKey(
                limit_choices_to={"organization__type": "MAIN"},
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="base.entity",
            ),
        ),
    ]
