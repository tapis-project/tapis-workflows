# Generated by Django 4.0.1 on 2022-02-18 20:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0016_alter_pipeline_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='context',
            name='dockerfile_path',
            field=models.CharField(default='Dockerfile', max_length=255),
        ),
        migrations.AlterField(
            model_name='pipeline',
            name='dockerfile_path',
            field=models.CharField(default='Dockerfile', max_length=255),
        ),
    ]