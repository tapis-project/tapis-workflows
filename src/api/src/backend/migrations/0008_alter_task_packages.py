# Generated by Django 4.1.2 on 2023-02-28 22:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0007_event_cron_task__if_task_code_task_command_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='packages',
            field=models.JSONField(default=list, null=True),
        ),
    ]