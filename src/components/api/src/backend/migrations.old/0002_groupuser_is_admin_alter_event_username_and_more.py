# Generated by Django 4.0.1 on 2022-03-22 00:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupuser',
            name='is_admin',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='event',
            name='username',
            field=models.CharField(max_length=64),
        ),
        migrations.AlterField(
            model_name='groupuser',
            name='username',
            field=models.CharField(max_length=64),
        ),
        migrations.AlterField(
            model_name='identity',
            name='username',
            field=models.CharField(max_length=64),
        ),
    ]
