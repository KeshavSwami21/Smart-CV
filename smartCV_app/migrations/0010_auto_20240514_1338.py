# Generated by Django 3.2.12 on 2024-05-14 08:08

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('smartCV_app', '0009_auto_20240513_1344'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logging',
            name='timestamp',
            field=models.TimeField(default=datetime.datetime(2024, 5, 14, 13, 38, 20, 521246)),
        ),
        migrations.AlterField(
            model_name='resumedata',
            name='education',
            field=models.JSONField(default=list),
        ),
        migrations.AlterField(
            model_name='resumedata',
            name='experience',
            field=models.JSONField(default=list),
        ),
        migrations.AlterField(
            model_name='resumedata',
            name='job_description_skills',
            field=models.JSONField(default=list),
        ),
        migrations.AlterField(
            model_name='resumedata',
            name='matching_skills',
            field=models.JSONField(default=list),
        ),
        migrations.AlterField(
            model_name='resumedata',
            name='missing_skills',
            field=models.JSONField(default=list),
        ),
        migrations.AlterField(
            model_name='resumedata',
            name='resume_skills',
            field=models.JSONField(default=list),
        ),
        migrations.AlterField(
            model_name='selectedskills',
            name='resume_serial_number',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='selected_skills', to='smartCV_app.resumedata'),
        ),
        migrations.AlterField(
            model_name='selectedskills',
            name='skill',
            field=models.JSONField(default=list),
        ),
    ]
