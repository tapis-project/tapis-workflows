# Generated by Django 4.0.1 on 2022-07-22 05:47

import backend.models
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
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
                ('system_id', models.CharField(max_length=80, null=True)),
                ('archive_dir', models.CharField(max_length=256, null=True)),
                ('endpoint', models.CharField(max_length=256, null=True)),
                ('bucket', models.CharField(max_length=64, null=True)),
                ('region', models.CharField(max_length=64, null=True)),
                ('host', models.CharField(max_length=256, null=True)),
                ('port', models.PositiveIntegerField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Context',
            fields=[
                ('branch', models.CharField(max_length=128, null=True)),
                ('recipe_file_path', models.CharField(max_length=255, null=True)),
                ('sub_path', models.CharField(max_length=255, null=True)),
                ('tag', models.CharField(max_length=128, null=True)),
                ('type', models.CharField(choices=[('github', 'github'), ('gitlab', 'gitlab'), ('dockerhub', 'dockerhub')], max_length=32)),
                ('url', models.CharField(max_length=128, validators=[backend.models.validate_ctx_dest_url])),
                ('uuid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('visibility', models.CharField(choices=[('public', 'public'), ('private', 'private')], max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='Credentials',
            fields=[
                ('sk_id', models.CharField(max_length=128, primary_key=True, serialize=False, unique=True)),
                ('owner', models.CharField(max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4)),
            ],
        ),
        migrations.CreateModel(
            name='Destination',
            fields=[
                ('tag', models.CharField(max_length=128, null=True)),
                ('filename', models.CharField(max_length=128, null=True)),
                ('type', models.CharField(choices=[('dockerhub', 'dockerhub'), ('local', 'local')], max_length=32)),
                ('url', models.CharField(max_length=255, null=True, validators=[backend.models.validate_ctx_dest_url])),
                ('uuid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('branch', models.CharField(max_length=255, null=True)),
                ('commit', models.TextField(max_length=255, null=True)),
                ('commit_sha', models.CharField(max_length=128, null=True)),
                ('context_url', models.CharField(max_length=128, null=True)),
                ('directives', models.JSONField(null=True)),
                ('message', models.TextField()),
                ('source', models.CharField(max_length=255)),
                ('username', models.CharField(max_length=64, null=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.CharField(max_length=128, unique=True, validators=[backend.models.validate_id])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('owner', models.CharField(max_length=64)),
                ('tenant_id', models.CharField(max_length=128)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Pipeline',
            fields=[
                ('id', models.CharField(max_length=128, validators=[backend.models.validate_id])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('invocation_mode', models.CharField(default='async', max_length=16)),
                ('max_exec_time', models.BigIntegerField(default=10800, validators=[django.core.validators.MaxValueValidator(10800), django.core.validators.MinValueValidator(1)])),
                ('max_retries', models.IntegerField(default=0)),
                ('owner', models.CharField(max_length=64)),
                ('retry_policy', models.CharField(default='exponential_backoff', max_length=32)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='PipelineRun',
            fields=[
                ('status', models.CharField(choices=[('pending', 'pending'), ('active', 'active'), ('backoff', 'backoff'), ('completed', 'completed'), ('failed', 'failed'), ('suspended', 'suspended'), ('terminated', 'terminated')], default='pending', max_length=16)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('ended_at', models.DateTimeField()),
                ('uuid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('pipeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='runs', to='backend.pipeline')),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.CharField(max_length=128, validators=[backend.models.validate_id])),
                ('cache', models.BooleanField(null=True)),
                ('depends_on', models.JSONField(default=list, null=True)),
                ('description', models.TextField(null=True)),
                ('input', models.JSONField(null=True)),
                ('invocation_mode', models.CharField(default='async', max_length=16)),
                ('max_exec_time', models.BigIntegerField(default=3600, validators=[django.core.validators.MaxValueValidator(10800), django.core.validators.MinValueValidator(1)])),
                ('max_retries', models.IntegerField(default=0)),
                ('output', models.JSONField(null=True)),
                ('poll', models.BooleanField(null=True)),
                ('retries', models.IntegerField(default=0)),
                ('retry_policy', models.CharField(default='exponential_backoff', max_length=32)),
                ('type', models.CharField(choices=[('image_build', 'image_build'), ('container_run', 'container_run'), ('request', 'request'), ('tapis_job', 'tapis_job'), ('tapis_actor', 'tapis_actor')], max_length=32)),
                ('uuid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('builder', models.CharField(choices=[('kaniko', 'kaniko'), ('singularity', 'singularity')], max_length=32, null=True)),
                ('data', models.JSONField(null=True)),
                ('headers', models.JSONField(null=True)),
                ('http_method', models.CharField(choices=[('get', 'get'), ('post', 'post'), ('put', 'put'), ('patch', 'patch'), ('delete', 'delete')], max_length=32, null=True)),
                ('protocol', models.CharField(choices=[('http', 'http'), ('ssh', 'ssh'), ('sftp', 'sftp'), ('ftp', 'ftp'), ('ftps', 'ftps')], max_length=32, null=True)),
                ('query_params', models.JSONField(null=True)),
                ('url', models.CharField(max_length=255, null=True)),
                ('image', models.CharField(max_length=128, null=True)),
                ('tapis_job_def', models.JSONField(null=True)),
                ('tapis_actor_id', models.CharField(max_length=128, null=True)),
                ('auth', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.credentials')),
                ('context', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.context')),
                ('destination', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.destination')),
                ('pipeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='backend.pipeline')),
            ],
        ),
        migrations.CreateModel(
            name='TaskExecution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('pending', 'pending'), ('active', 'active'), ('backoff', 'backoff'), ('completed', 'completed'), ('failed', 'failed'), ('suspended', 'suspended'), ('terminated', 'terminated')], default='pending', max_length=16)),
                ('ended_at', models.DateTimeField()),
                ('uuid', models.UUIDField(default=uuid.uuid4)),
                ('pipeline_run', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='task_executions', to='backend.pipelinerun')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='task_executions', to='backend.task')),
            ],
        ),
        migrations.CreateModel(
            name='PipelineArchive',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('archive', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pipelines', to='backend.archive')),
                ('pipeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='archives', to='backend.pipeline')),
            ],
        ),
        migrations.AddField(
            model_name='pipeline',
            name='current_run',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='backend.pipelinerun'),
        ),
        migrations.AddField(
            model_name='pipeline',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pipelines', to='backend.group'),
        ),
        migrations.AddField(
            model_name='pipeline',
            name='last_run',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='backend.pipelinerun'),
        ),
        migrations.CreateModel(
            name='Identity',
            fields=[
                ('name', models.CharField(max_length=64)),
                ('description', models.TextField(null=True)),
                ('type', models.CharField(choices=[('github', 'github'), ('gitlab', 'gitlab'), ('dockerhub', 'dockerhub')], max_length=32)),
                ('owner', models.CharField(max_length=64)),
                ('tenant_id', models.CharField(max_length=128)),
                ('uuid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('credentials', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='backend.credentials')),
            ],
        ),
        migrations.CreateModel(
            name='GroupUser',
            fields=[
                ('username', models.CharField(max_length=64)),
                ('is_admin', models.BooleanField(default=False)),
                ('uuid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='users', to='backend.group')),
            ],
        ),
        migrations.AddIndex(
            model_name='group',
            index=models.Index(fields=['owner', 'tenant_id'], name='backend_gro_owner_76335a_idx'),
        ),
        migrations.AddConstraint(
            model_name='group',
            constraint=models.UniqueConstraint(fields=('id', 'tenant_id'), name='group_id_tenant_id'),
        ),
        migrations.AddField(
            model_name='event',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='events', to='backend.group'),
        ),
        migrations.AddField(
            model_name='event',
            name='pipeline',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='events', to='backend.pipeline'),
        ),
        migrations.AddField(
            model_name='destination',
            name='credentials',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.credentials'),
        ),
        migrations.AddField(
            model_name='destination',
            name='identity',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.identity'),
        ),
        migrations.AddField(
            model_name='context',
            name='credentials',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.credentials'),
        ),
        migrations.AddField(
            model_name='context',
            name='identity',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.identity'),
        ),
        migrations.AddField(
            model_name='archive',
            name='credentials',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.credentials'),
        ),
        migrations.AddField(
            model_name='archive',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='archives', to='backend.group'),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['id', 'pipeline_id'], name='backend_tas_id_1bd36f_idx'),
        ),
        migrations.AddConstraint(
            model_name='task',
            constraint=models.UniqueConstraint(fields=('id', 'pipeline_id'), name='task_id_pipeline_id'),
        ),
        migrations.AddConstraint(
            model_name='pipelinearchive',
            constraint=models.UniqueConstraint(fields=('pipeline', 'archive'), name='pipelinearchive_pipeline_archive'),
        ),
        migrations.AddConstraint(
            model_name='pipeline',
            constraint=models.UniqueConstraint(fields=('id', 'group'), name='pipeline_id_group'),
        ),
        migrations.AddConstraint(
            model_name='identity',
            constraint=models.UniqueConstraint(fields=('name', 'owner', 'tenant_id'), name='identity_name_owner_tenant_id'),
        ),
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['pipeline_id'], name='backend_eve_pipelin_5ff4d0_idx'),
        ),
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['username'], name='backend_eve_usernam_0004a2_idx'),
        ),
        migrations.AddIndex(
            model_name='archive',
            index=models.Index(fields=['id', 'group_id'], name='backend_arc_id_20d14d_idx'),
        ),
        migrations.AddConstraint(
            model_name='archive',
            constraint=models.UniqueConstraint(fields=('id', 'group_id'), name='archive_id_group_id'),
        ),
    ]
