# Generated by Django 4.0.1 on 2022-06-20 18:07

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Archive',
            fields=[
                ('id', models.CharField(max_length=128)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('identity_uuid', models.UUIDField(null=True)),
                ('owner', models.CharField(max_length=64)),
                ('type', models.CharField(choices=[('system', 'system'), ('s3', 's3'), ('irods', 'irods')], max_length=32)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('system_id', models.CharField(max_length=80)),
                ('credentials', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.credentials')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='archives', to='backend.group')),
            ],
        ),
        migrations.AddIndex(
            model_name='archive',
            index=models.Index(fields=['id', 'group_id'], name='backend_arc_id_20d14d_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='archive',
            unique_together={('id', 'group_id')},
        ),
        migrations.AddField(
            model_name='archive',
            name='archive_dir',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='archive',
            name='bucket',
            field=models.CharField(max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='archive',
            name='endpoint',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='archive',
            name='host',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='archive',
            name='port',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='archive',
            name='region',
            field=models.CharField(max_length=64, null=True),
        ),
        migrations.AlterField(
            model_name='archive',
            name='system_id',
            field=models.CharField(max_length=80, null=True),
        ),
    ]