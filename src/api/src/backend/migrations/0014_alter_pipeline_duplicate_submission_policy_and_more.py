# Generated by Django 4.1.2 on 2023-04-10 23:31

import backend.views.http.requests
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0013_pipeline_params'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pipeline',
            name='duplicate_submission_policy',
            field=models.CharField(choices=[(backend.views.http.requests.EnumDuplicateSubmissionPolicy['Allow'], backend.views.http.requests.EnumDuplicateSubmissionPolicy['Allow']), (backend.views.http.requests.EnumDuplicateSubmissionPolicy['Deny'], backend.views.http.requests.EnumDuplicateSubmissionPolicy['Deny']), (backend.views.http.requests.EnumDuplicateSubmissionPolicy['Terminate'], backend.views.http.requests.EnumDuplicateSubmissionPolicy['Terminate']), (backend.views.http.requests.EnumDuplicateSubmissionPolicy['Defer'], backend.views.http.requests.EnumDuplicateSubmissionPolicy['Defer'])], default=backend.views.http.requests.EnumDuplicateSubmissionPolicy['Terminate'], max_length=32),
        ),
        migrations.AlterField(
            model_name='task',
            name='runtime',
            field=models.CharField(choices=[(backend.views.http.requests.EnumRuntimeEnvironment['Python39'], backend.views.http.requests.EnumRuntimeEnvironment['Python39']), (backend.views.http.requests.EnumRuntimeEnvironment['PythonSingularity'], backend.views.http.requests.EnumRuntimeEnvironment['PythonSingularity'])], max_length=64, null=True),
        ),
    ]