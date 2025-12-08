from django.db import migrations


def remove_private_defenses_related_to_pre_admissions(apps, _):
    PrivateDefense = apps.get_model('parcours_doctoral', 'PrivateDefense')

    PrivateDefense.objects.filter(parcours_doctoral__admission__type='PRE_ADMISSION').delete()


class Migration(migrations.Migration):

    dependencies = [
        ("parcours_doctoral", "0036_scebmanager"),
    ]

    operations = [
        migrations.RunPython(
            code=remove_private_defenses_related_to_pre_admissions,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
