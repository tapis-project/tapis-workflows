# Generated by Django 4.0.1 on 2022-02-10 19:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=255)),
                ('group', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='backend.group')),
            ],
        ),
    ]
