import uuid, re

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError

ONE_HOUR_IN_SEC = 3600

ACTION_TYPE_IMAGE_BUILD = "image_build"
ACTION_TYPE_CONTAINER_RUN = "container_run"
ACTION_TYPE_WEBHOOK_NOTIFICATION = "webhook_notification"
ACTION_TYPE_TAPIS_JOB = "tapis_job"
ACTION_TYPE_TAPIS_ACTOR = "tapis_actor"
ACTION_TYPES = [
    (ACTION_TYPE_IMAGE_BUILD, "image_build"),
    (ACTION_TYPE_CONTAINER_RUN, "container_run"),
    (ACTION_TYPE_WEBHOOK_NOTIFICATION, "webhook_notification"),
    (ACTION_TYPE_TAPIS_JOB, "tapis_job"),
    (ACTION_TYPE_TAPIS_ACTOR, "tapis_actor"),
]

ARCHIVE_TYPE_SYSTEM = "system"
ARCHIVE_TYPE_S3 = "s3"
ARCHIVE_TYPE_IRODS = "irods"
ARCHIVE_TYPES = [
    (ARCHIVE_TYPE_SYSTEM, "system"),
    (ARCHIVE_TYPE_S3, "s3"),
    (ARCHIVE_TYPE_IRODS, "irods")
]

DEFAULT_ARCHIVE_DIR = "/workflows/archive/"

IMAGE_BUILDER_KANIKO = "kaniko"
IMAGE_BUILDER_SINGULARITY = "singularity"
IMAGE_BUILDERS = [
    (IMAGE_BUILDER_KANIKO, "kaniko"),
    (IMAGE_BUILDER_SINGULARITY, "singularity"),
]

HTTP_METHOD_GET = "get"
HTTP_METHOD_POST = "post"
HTTP_METHOD_PUT = "put"
HTTP_METHOD_PATCH = "patch"
HTTP_METHOD_DELETE = "delete"
ACTION_HTTP_METHODS = [
    (HTTP_METHOD_GET, "get"),
    (HTTP_METHOD_POST, "post"),
    (HTTP_METHOD_PUT, "put"),
    (HTTP_METHOD_PATCH, "patch"),
    (HTTP_METHOD_DELETE, "delete"),
]

CONTEXT_TYPE_GITHUB = "github"
CONTEXT_TYPE_GITLAB = "gitlab"
CONTEXT_TYPE_DOCKERHUB = "dockerhub"
CONTEXT_TYPES = [
    (CONTEXT_TYPE_GITHUB, "github"),
    (CONTEXT_TYPE_GITLAB, "gitlab"),
    (CONTEXT_TYPE_DOCKERHUB, "dockerhub"),
]

DESTINATION_TYPE_DOCKERHUB = "dockerhub"
DESTINATION_TYPE_DOCKERHUB_LOCAL = "dockerhub_local"
DESTINATION_TYPE_LOCAL = "local"
DESTINATION_TYPE_S3 = "s3"
DESTINATION_TYPES = [
    (DESTINATION_TYPE_DOCKERHUB, "dockerhub"),
    (DESTINATION_TYPE_LOCAL, "local")
    # TODO support s3 destinations
    # TODO support local destination
    # TODO support local dockerhub
]

IDENTITY_TYPES = CONTEXT_TYPES

DEFAULT_RECIPE_FILE_PATH = "Dockerfile"

GROUP_STATUS_DISABLED = "disabled"
GROUP_STATUS_ENABLED = "enabled"
GROUP_STATUSES = [
    (GROUP_STATUS_DISABLED, "disabled"),
    (GROUP_STATUS_ENABLED, "enabled")
]

PERMISSION_READ = "read"
PERMISSION_WRITE = "write"
PERMISSION_MODIFY = "modify"
PERMISSIONS = [
    (PERMISSION_READ, "read"),
    (PERMISSION_WRITE, "write"), # Write implies read
    (PERMISSION_MODIFY, "modify"), # Modify implies write which implies read
]

ACCESS_CONTROL_ALLOW = "allow"
ACCESS_CONTROL_DENY = "deny"
ACCESS_CONTROLS = [
    (ACCESS_CONTROL_ALLOW, "allow"),
    (ACCESS_CONTROL_DENY, "deny")
]

STATUS_QUEUED = "queued"
STATUS_IN_PROGRESS = "in_progress"
STATUS_PUSHING = "pushing"
STATUS_ERROR = "error"
STATUS_SUCCESS = "success"
STATUSES = [
    (STATUS_QUEUED, "queued"),
    (STATUS_IN_PROGRESS, "in_progress"),
    (STATUS_PUSHING, "pushing"),
    (STATUS_ERROR, "error"),
    (STATUS_SUCCESS, "success"),
]

RUN_STATUS_ACTIVE = "active"
RUN_STATUS_PENDING = "pending"
RUN_STATUS_COMPLETED = "completed"
RUN_STATUS_FAILED = "failed"
RUN_STATUS_SUSPENDED = "suspended"
RUN_STATUS_TERMINATED = "terminated"

RUN_STATUSES = [
    (RUN_STATUS_PENDING, "pending"),
    (RUN_STATUS_ACTIVE, "active"),
    (RUN_STATUS_COMPLETED, "completed"),
    (RUN_STATUS_FAILED, "failed"),
    (RUN_STATUS_SUSPENDED, "suspended"),
    (RUN_STATUS_TERMINATED, "terminated"),
]

ACTION_EXECUTION_STATUSES = RUN_STATUSES

VISIBILITY_PUBLIC = "public"
VISIBILITY_PRIVATE = "private"
VISIBILITY_TYPES = [
    (VISIBILITY_PUBLIC, "public"),
    (VISIBILITY_PRIVATE, "private")
]

### Validators ###

def validate_id(value):
    pattern = re.compile(r"^[A-Z0-9\-_]+$")
    if pattern.match(value) == None:
        raise ValidationError("`id` property must only contain alphanumeric characters, underscores, and hypens")

def validate_ctx_dest_url(value):
    pattern = re.compile(r"^[a-zA-Z0-9-_]+/[a-zA-Z0-9-_]+$")
    if pattern.match(value) == None:
        raise ValidationError("`url` must follow the format:  `<username>/<name>`")

##################

class Action(models.Model):
    id = models.CharField(validators=[validate_id], max_length=128)
    cache = models.BooleanField(null=True)
    depends_on = models.JSONField(null=True, default=list)
    description = models.TextField(null=True)
    input = models.JSONField(null=True)
    output = models.JSONField(null=True)
    pipeline = models.ForeignKey("backend.Pipeline", related_name="actions", on_delete=models.CASCADE)
    poll = models.BooleanField(null=True)
    retries = models.IntegerField(default=0)
    type = models.CharField(max_length=32, choices=ACTION_TYPES)
    ttl = models.BigIntegerField(
        default=ONE_HOUR_IN_SEC,
        validators=[MaxValueValidator(ONE_HOUR_IN_SEC*3), MinValueValidator(1)]
    )
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # Image build specific properties
    builder = models.CharField(max_length=32, choices=IMAGE_BUILDERS, null=True)
    context = models.OneToOneField("backend.Context", null=True, on_delete=models.CASCADE)
    destination = models.OneToOneField("backend.Destination", null=True, on_delete=models.CASCADE)
    
    # Webhook notification specific properties
    auth = models.ForeignKey("backend.Credentials", null=True, on_delete=models.CASCADE)
    data = models.JSONField(null=True)
    headers = models.JSONField(null=True)
    http_method = models.CharField(max_length=32, choices=ACTION_HTTP_METHODS, null=True)
    query_params = models.JSONField(null=True)
    url = models.CharField(max_length=255, null=True)
    
    # Container run specific properties
    # Full image name for container run. includes scheme.
    image = models.CharField(max_length=128, null=True)

    # Tapis job specific properties
    tapis_job_def = models.JSONField(null=True)

    # Tapis actor specific properties
    tapis_actor_id = models.CharField(max_length=128, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["id", "pipeline_id"],
                name="action_id_pipeline_id"
            )
        ]
        indexes = [
            models.Index(fields=["id", "pipeline_id"])
        ]

class Archive(models.Model):
    id = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    credentials = models.OneToOneField("backend.Credentials", null=True, on_delete=models.CASCADE)
    group = models.ForeignKey("backend.Group", related_name="archives", on_delete=models.CASCADE)
    identity_uuid = models.UUIDField(null=True)
    owner = models.CharField(max_length=64)
    type = models.CharField(max_length=32, choices=ARCHIVE_TYPES)
    updated_at = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # System specific properties
    system_id = models.CharField(max_length=80, null=True) # Same max length as Tapis System
    archive_dir = models.CharField(max_length=256, null=True)

    # S3 specific properties
    endpoint = models.CharField(max_length=256, null=True)
    bucket = models.CharField(max_length=64, null=True)
    region = models.CharField(max_length=64, null=True)

    # IRODS specific properties
    host = models.CharField(max_length=256, null=True)
    port = models.PositiveIntegerField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["id", "group_id"],
                name="archive_id_group_id"
            )
        ]
        indexes = [
            models.Index(fields=["id", "group_id"])
        ]

class ActionExecution(models.Model):
    action = models.ForeignKey("backend.Action", related_name="action_executions", on_delete=models.CASCADE)
    pipeline_run = models.ForeignKey("backend.PipelineRun", related_name="action_executions", on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=16, choices=ACTION_EXECUTION_STATUSES, default=RUN_STATUS_PENDING)
    ended_at = models.DateTimeField()
    uuid = models.UUIDField(default=uuid.uuid4)

class Credentials(models.Model):
    sk_id = models.CharField(primary_key=True, max_length=128, unique=True)
    owner = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(default=uuid.uuid4)

class Context(models.Model):
    branch = models.CharField(max_length=128, null=True)
    credentials = models.OneToOneField("backend.Credentials", null=True, on_delete=models.CASCADE)
    recipe_file_path = models.CharField(max_length=255, null=True)
    sub_path = models.CharField(max_length=255, null=True)
    tag = models.CharField(max_length=128, null=True)
    type = models.CharField(max_length=32, choices=CONTEXT_TYPES)
    url = models.CharField(validators=[validate_ctx_dest_url], max_length=128)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    visibility = models.CharField(max_length=32, choices=VISIBILITY_TYPES)
    identity = models.ForeignKey("backend.Identity", null=True, on_delete=models.CASCADE)

class Destination(models.Model):
    credentials = models.OneToOneField("backend.Credentials", null=True, on_delete=models.CASCADE)
    tag = models.CharField(max_length=128, null=True)
    filename = models.CharField(max_length=128, null=True)
    type = models.CharField(max_length=32, choices=DESTINATION_TYPES)
    url = models.CharField(validators=[validate_ctx_dest_url], max_length=255, null=True)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    identity = models.ForeignKey("backend.Identity", null=True, on_delete=models.CASCADE)

class Event(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    branch = models.CharField(max_length=255, null=True)
    commit = models.TextField(max_length=255, null=True)
    commit_sha = models.CharField(max_length=128, null=True)
    context_url = models.CharField(max_length=128, null=True)
    directives = models.JSONField(null=True)
    message = models.TextField()
    group = models.ForeignKey("backend.Group", related_name="events", null=True, on_delete=models.CASCADE)
    pipeline = models.ForeignKey("backend.Pipeline", related_name="events", null=True, on_delete=models.CASCADE)
    source = models.CharField(max_length=255)
    username = models.CharField(max_length=64, null=True)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    class Meta:
        indexes = [
            models.Index(fields=["pipeline_id"]),
            models.Index(fields=["username"])
        ]

class Group(models.Model):
    id = models.CharField(validators=[validate_id], max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.CharField(max_length=64)
    tenant_id = models.CharField(max_length=128)
    updated_at = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    class Meta:
        indexes = [
            models.Index(fields=["owner", "tenant_id"])
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["id", "tenant_id"],
                name="group_id_tenant_id"
            )
        ]

class GroupUser(models.Model):
    group = models.ForeignKey("backend.Group", related_name="users", on_delete=models.CASCADE)
    username = models.CharField(max_length=64)
    is_admin = models.BooleanField(default=False)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)

class Identity(models.Model):
    name = models.CharField(max_length=64)
    description = models.TextField(null=True)
    type = models.CharField(max_length=32, choices=IDENTITY_TYPES)
    owner = models.CharField(max_length=64)
    tenant_id = models.CharField(max_length=128)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    credentials = models.OneToOneField("backend.Credentials", on_delete=models.CASCADE)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "owner", "tenant_id"],
                name="identity_name_owner_tenant_id"
            )
        ]

class Pipeline(models.Model):
    id = models.CharField(validators=[validate_id], max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    group = models.ForeignKey("backend.Group", related_name="pipelines", on_delete=models.CASCADE)
    owner = models.CharField(max_length=64)
    updated_at = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    current_run = models.ForeignKey("backend.PipelineRun", related_name="+", null=True, on_delete=models.CASCADE)
    last_run = models.ForeignKey("backend.PipelineRun", related_name="+", null=True, on_delete=models.CASCADE)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["id", "group"],
                name="pipeline_id_group"
            )
        ]

class PipelineArchive(models.Model):
    pipeline = models.ForeignKey("backend.Pipeline", related_name="archives", on_delete=models.CASCADE)
    archive = models.ForeignKey("backend.Archive", related_name="pipelines", on_delete=models.CASCADE)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["pipeline", "archive"],
                name="pipelinearchive_pipeline_archive"
            )
        ]

class PipelineRun(models.Model):
    pipeline = models.ForeignKey("backend.Pipeline", related_name="runs", on_delete=models.CASCADE)
    status = models.CharField(max_length=16, choices=RUN_STATUSES, default=RUN_STATUS_PENDING)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField()
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)