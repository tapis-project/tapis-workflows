# Generated by Django 4.1.2 on 2023-11-28 17:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0027_alter_pipelinerun_status_alter_taskexecution_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='conditions',
            field=models.JSONField(default=list, null=True),
        ),
    ]
