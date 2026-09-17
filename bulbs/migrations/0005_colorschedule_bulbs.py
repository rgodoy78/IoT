from django.db import migrations, models


def migrate_bulb_to_bulbs(apps, schema_editor):
    ColorSchedule = apps.get_model("bulbs", "ColorSchedule")
    for schedule in ColorSchedule.objects.all():
        if schedule.bulb_id:
            schedule.bulbs.add(schedule.bulb_id)


def migrate_bulbs_to_bulb(apps, schema_editor):
    ColorSchedule = apps.get_model("bulbs", "ColorSchedule")
    for schedule in ColorSchedule.objects.all():
        first_bulb = schedule.bulbs.first()
        if first_bulb:
            schedule.bulb_id = first_bulb.pk
            schedule.save(update_fields=["bulb"])


class Migration(migrations.Migration):

    dependencies = [
        ('bulbs', '0004_colorschedule'),
    ]

    operations = [
        migrations.AddField(
            model_name='colorschedule',
            name='bulbs',
            field=models.ManyToManyField(related_name='schedules_new', to='bulbs.bulb', verbose_name='Ampolletas'),
        ),
        migrations.RunPython(migrate_bulb_to_bulbs, migrate_bulbs_to_bulb),
        migrations.RemoveField(
            model_name='colorschedule',
            name='bulb',
        ),
        migrations.AlterField(
            model_name='colorschedule',
            name='bulbs',
            field=models.ManyToManyField(related_name='schedules', to='bulbs.bulb', verbose_name='Ampolletas'),
        ),
        migrations.AlterModelOptions(
            name='colorschedule',
            options={'ordering': ['start_time'], 'verbose_name': 'Programación de color', 'verbose_name_plural': 'Programaciones de color'},
        ),
    ]
