# Generated by Django 4.1.2 on 2023-03-09 20:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0009_pipeline_env'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pipeline',
            name='env',
            field=models.JSONField(null=True),
        ),
    ]