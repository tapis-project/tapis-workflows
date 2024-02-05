# Generated by Django 4.1.2 on 2023-08-02 20:52

import backend.views.http.requests
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0017_alter_task_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='type',
            field=models.CharField(choices=[(backend.views.http.requests.EnumTaskType['ImageBuild'], backend.views.http.requests.EnumTaskType['ImageBuild']), (backend.views.http.requests.EnumTaskType['ContainerRun'], backend.views.http.requests.EnumTaskType['Application']), (backend.views.http.requests.EnumTaskType['Application'], backend.views.http.requests.EnumTaskType['ContainerRun']), (backend.views.http.requests.EnumTaskType['Request'], backend.views.http.requests.EnumTaskType['Request']), (backend.views.http.requests.EnumTaskType['Function'], backend.views.http.requests.EnumTaskType['Function']), (backend.views.http.requests.EnumTaskType['TapisJob'], backend.views.http.requests.EnumTaskType['TapisJob']), (backend.views.http.requests.EnumTaskType['TapisActor'], backend.views.http.requests.EnumTaskType['TapisActor'])], max_length=32),
        ),
    ]