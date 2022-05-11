import uuid

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

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

IMAGE_BUILDER_KANIKO = "kaniko"
IMAGE_BUILDERS = [
    (IMAGE_BUILDER_KANIKO, "kaniko"),
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
CONTEXT_TYPES = [
    (CONTEXT_TYPE_GITHUB, "github"),
    (CONTEXT_TYPE_GITLAB, "gitlab"),
]

DESTINATION_TYPE_REGISTRY = "dockerhub"
DESTINATION_TYPES = [
    (DESTINATION_TYPE_REGISTRY, "dockerhub")
    # NOTE support s3 destinations?
]

DEFAULT_DOCKERFILE_PATH = "Dockerfile"

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

VISIBILITY_PUBLIC = "public"
VISIBILITY_PRIVATE = "private"
VISIBILITY_TYPES = [
    (VISIBILITY_PUBLIC, "public"),
    (VISIBILITY_PRIVATE, "private")
]

class Action(models.Model):
    id = models.CharField(max_length=128)
    auth = models.ForeignKey("backend.Credentials", null=True, on_delete=models.CASCADE)
    auto_build = models.BooleanField(null=True)
    builder = models.CharField(max_length=32, choices=IMAGE_BUILDERS, null=True)
    cache = models.BooleanField(null=True)
    context = models.OneToOneField("backend.Context", null=True, on_delete=models.CASCADE)
    depends_on = models.JSONField(null=True, default=list)
    description = models.TextField(null=True)
    destination = models.OneToOneField("backend.Destination", null=True, on_delete=models.CASCADE)
    data = models.JSONField(null=True)
    headers = models.JSONField(null=True)
    http_method = models.CharField(max_length=32, choices=ACTION_HTTP_METHODS, null=True)
    image = models.CharField(max_length=128, null=True)
    input = models.JSONField(null=True)
    output = models.JSONField(null=True)
    poll = models.BooleanField(null=True)
    query_params = models.JSONField(null=True)
    pipeline = models.ForeignKey("backend.Pipeline", related_name="actions", on_delete=models.CASCADE)
    retries = models.IntegerField(default=0)
    tapis_job_def = models.JSONField(null=True)
    tapis_actor_id = models.CharField(max_length=128, null=True)
    type = models.CharField(max_length=32, choices=ACTION_TYPES)
    ttl = models.BigIntegerField(
        default=ONE_HOUR_IN_SEC,
        validators=[MaxValueValidator(ONE_HOUR_IN_SEC*3), MinValueValidator(1)]
    )
    url = models.CharField(max_length=255, null=True)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    class Meta:
        unique_together = [["id", "pipeline_id"]]
        indexes = [
            models.Index(fields=["id", "pipeline_id"])
        ]

class Identity(models.Model):
    type = models.CharField(max_length=32, choices=CONTEXT_TYPES)
    owner = models.CharField(max_length=64)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    credentials = models.OneToOneField("backend.Credentials", on_delete=models.CASCADE)
    class Meta:
        unique_together = [["owner", "type"]]

class Build(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    event = models.OneToOneField("backend.Event", on_delete=models.CASCADE)
    group = models.ForeignKey("backend.Group", related_name="builds", on_delete=models.CASCADE)
    pipeline = models.ForeignKey("backend.Pipeline", related_name="builds", on_delete=models.CASCADE)
    status = models.CharField(max_length=32, choices=STATUSES, default=STATUS_QUEUED)
    updated_at = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    class Meta:
        indexes = [
            models.Index(fields=["pipeline_id"])
        ]

class Credentials(models.Model):
    sk_id = models.CharField(primary_key=True, max_length=128, unique=True)
    owner = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(default=uuid.uuid4)

class Context(models.Model):
    branch = models.CharField(max_length=128)
    credentials = models.OneToOneField("backend.Credentials", null=True, on_delete=models.CASCADE)
    dockerfile_path = models.CharField(max_length=255, default=DEFAULT_DOCKERFILE_PATH)
    sub_path = models.CharField(max_length=255, null=True)
    type = models.CharField(max_length=32, choices=CONTEXT_TYPES)
    url = models.CharField(max_length=128)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    visibility = models.CharField(max_length=32, choices=VISIBILITY_TYPES)
    identity = models.ForeignKey("backend.Identity", null=True, on_delete=models.DO_NOTHING)

class Destination(models.Model):
    credentials = models.OneToOneField("backend.Credentials", on_delete=models.CASCADE)
    tag = models.CharField(max_length=128)
    type = models.CharField(max_length=32, choices=DESTINATION_TYPES)
    url = models.CharField(max_length=255)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    identity = models.ForeignKey("backend.Identity", null=True, on_delete=models.DO_NOTHING)

class Group(models.Model):
    id = models.CharField(primary_key=True, max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.CharField(max_length=64)
    updated_at = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(default=uuid.uuid4)
    class Meta:
        indexes = [
            models.Index(fields=["owner"])
        ]

class GroupUser(models.Model):
    group = models.ForeignKey("backend.Group", related_name="users", on_delete=models.CASCADE)
    username = models.CharField(max_length=64)
    is_admin = models.BooleanField(default=False)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    class Meta:
        indexes = [
            models.Index(fields=["username"])
        ]

class Event(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    branch = models.CharField(max_length=255, null=True)
    commit = models.TextField(max_length=255, null=True)
    commit_sha = models.CharField(max_length=128, null=True)
    context_url = models.CharField(max_length=128, null=True)
    directives = models.JSONField(null=True)
    message = models.TextField()
    pipeline = models.ForeignKey("backend.Pipeline", related_name="events", null=True, on_delete=models.CASCADE)
    source = models.CharField(max_length=255)
    username = models.CharField(max_length=64)
    identity = models.ForeignKey("backend.Identity", related_name="events", null=True, on_delete=models.CASCADE)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    class Meta:
        indexes = [
            models.Index(fields=["pipeline_id"])
        ]

class Pipeline(models.Model):
    id = models.CharField(primary_key=True, max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    group = models.ForeignKey("backend.Group", related_name="pipelines", on_delete=models.CASCADE)
    owner = models.CharField(max_length=64)
    updated_at = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(default=uuid.uuid4)

# class Policy(models.Model):      
#     pass