from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("parcours_doctoral", "0047_make_admission_facultative_2"),
    ]

    operations = [
        migrations.AlterField(
            model_name="parcoursdoctoral",
            name="admission_type",
            field=models.CharField(
                choices=[
                    ("ADMISSION", "ADMISSION"),
                    ("PRE_ADMISSION", "PRE_ADMISSION"),
                ],
                db_index=True,
                max_length=255,
                verbose_name="Admission type",
            ),
        ),
        migrations.AlterField(
            model_name="parcoursdoctoral",
            name="admission_approved_by_cdd_at",
            field=models.DateTimeField(
                verbose_name="Admission approved by CDD at",
            ),
        ),
        migrations.RemoveField(
            model_name="parcoursdoctoral",
            name="reference",
        ),
    ]
