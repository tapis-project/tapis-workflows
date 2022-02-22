import uuid

from django.db import models
from django.contrib.auth.models import User

ACTION_TYPE_CONTAINER_BUILD = "container_build"
ACTION_TYPE_CONTAINER_EXEC = "container_exec"
ACTION_TYPE_WEBHOOK_NOTIFICATION = "webhook_notification"
ACTION_TYPES = [
    (ACTION_TYPE_CONTAINER_BUILD, "container_build"),
    (ACTION_TYPE_CONTAINER_EXEC, "container_exec"),
    (ACTION_TYPE_WEBHOOK_NOTIFICATION, "webhook_notification"),
]

# ACTION_STAGE_PRE_BUILD = 0
ACTION_STAGE_BUILD = "build"
ACTION_STAGE_POST_BUILD = "post_build"
ACTION_STAGE_TYPES = [
    # TODO Support
    # (ACTION_STAGE_PRE_BUILD, "pre_build"),
    (ACTION_STAGE_BUILD, "build"),
    (ACTION_STAGE_POST_BUILD, "post_build"),
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
    ( DESTINATION_TYPE_REGISTRY, "dockerhub" )
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
    ( STATUS_QUEUED, "queued" ),
    ( STATUS_IN_PROGRESS, "in_progress" ),
    ( STATUS_PUSHING, "pushing" ),
    ( STATUS_ERROR, "error" ),
    ( STATUS_SUCCESS, "success" ),
]

VISIBILITY_PUBLIC = "public"
VISIBILITY_PRIVATE = "private"
VISIBILITY_TYPES = [
    ( VISIBILITY_PUBLIC, "public" ),
    ( VISIBILITY_PRIVATE, "private" )
]

class Account(models.Model):
    owner = models.CharField(max_length=128, primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4)

class Action(models.Model):
    auth = models.ForeignKey("backend.Credential", null=True, on_delete=models.CASCADE)
    builder = models.CharField(max_length=32, choices=IMAGE_BUILDERS, null=True)
    cache = models.BooleanField(default=False)
    context = models.OneToOneField("backend.Context", null=True, on_delete=models.CASCADE)
    data = models.JSONField(null=True)
    description = models.TextField(null=True)
    destination = models.OneToOneField("backend.Destination", null=True, on_delete=models.CASCADE)
    headers = models.JSONField(null=True)
    params = models.JSONField(null=True)
    pipeline = models.ForeignKey("backend.Pipeline", related_name="actions", on_delete=models.CASCADE)
    type = models.CharField(max_length=32, choices=ACTION_TYPES)
    http_method = models.CharField(max_length=32, choices=ACTION_HTTP_METHODS, null=True)
    name = models.CharField(max_length=128)
    stage = models.CharField(max_length=32, choices=ACTION_STAGE_TYPES)
    url = models.CharField(max_length=255, null=True)
    uuid = models.UUIDField(default=uuid.uuid4)
    class Meta:
        unique_together = [["name", "pipeline_id"]]

class Alias(models.Model):
    type = models.CharField(max_length=32, choices=CONTEXT_TYPES)
    account = models.ForeignKey("backend.Account", related_name="aliases", on_delete=models.CASCADE)
    group = models.ForeignKey("backend.Group", related_name="aliases", on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4)
    value = models.CharField(max_length=128)
    class Meta:
        unique_together = [["account_id", "value", "type"]]

class Build(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    event = models.OneToOneField("backend.Event", on_delete=models.CASCADE)
    group = models.ForeignKey("backend.Group", related_name="builds", on_delete=models.CASCADE)
    pipeline = models.ForeignKey("backend.Pipeline", related_name="builds", on_delete=models.CASCADE)
    status = models.CharField(max_length=32, choices=STATUSES, default=STATUS_QUEUED)
    updated_at = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(default=uuid.uuid4)

class Credential(models.Model):
    sk_id = models.CharField(max_length=128, unique=True)
    group = models.ForeignKey("backend.Group", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(default=uuid.uuid4)

class Context(models.Model):
    branch = models.CharField(max_length=128)
    credential = models.OneToOneField("backend.Credential", null=True, on_delete=models.CASCADE)
    dockerfile_path = models.CharField(max_length=255, default=DEFAULT_DOCKERFILE_PATH)
    sub_path = models.CharField(max_length=255, null=True)
    type = models.CharField(max_length=32, choices=CONTEXT_TYPES)
    url = models.CharField(max_length=128)
    uuiid = models.UUIDField(default=uuid.uuid4)
    visibility = models.CharField(max_length=32, choices=VISIBILITY_TYPES)

class Destination(models.Model):
    credential = models.OneToOneField("backend.Credential", on_delete=models.CASCADE)
    tag = models.CharField(max_length=128)
    type = models.CharField(max_length=32, choices=DESTINATION_TYPES)
    url = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid.uuid4)

class Group(models.Model):
    id = models.CharField(primary_key=True, max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.CharField(max_length=64)
    uuid = models.UUIDField(default=uuid.uuid4)
    indexes = [
        models.Index(fields=["owner"])
    ]

class GroupUser(models.Model):
    group = models.ForeignKey("backend.Group", related_name="users", on_delete=models.CASCADE)
    username = models.CharField(max_length=255)

class Event(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    branch = models.CharField(max_length=255)
    commit = models.TextField(max_length=255)
    commit_sha = models.CharField(max_length=128)
    context_url = models.CharField(max_length=128)
    message = models.TextField()
    pipeline = models.ForeignKey("backend.Pipeline", related_name="events", null=True, on_delete=models.CASCADE)
    source = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid.uuid4)

class Pipeline(models.Model):
    id = models.CharField(primary_key=True, max_length=128)
    auto_build = models.BooleanField(default=False)
    branch = models.CharField(max_length=255)
    builder = models.CharField(max_length=32, choices=IMAGE_BUILDERS, default=IMAGE_BUILDER_KANIKO)
    created_at = models.DateTimeField(auto_now_add=True)
    context_url = models.CharField(max_length=128)
    context_sub_path = models.CharField(max_length=255, null=True)
    context_type = models.CharField(max_length=32, choices=CONTEXT_TYPES)
    destination_type = models.CharField(max_length=32, choices=DESTINATION_TYPES)
    dockerfile_path = models.CharField(max_length=255, default=DEFAULT_DOCKERFILE_PATH)
    group = models.ForeignKey("backend.Group", on_delete=models.CASCADE)
    image_tag = models.CharField(max_length=64, null=True)
    owner = models.CharField(max_length=64)
    updated_at = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(default=uuid.uuid4)
    class Meta:
        unique_together = [["branch", "context_url", "context_type"]]

class Policy(models.Model):      
    context_commit: models.CharField(max_length=32, choices=ACCESS_CONTROLS, default=ACCESS_CONTROL_DENY)
    credentials: models.CharField(choices=PERMISSIONS, null=True)
    custom_tag: models.CharField(max_length=32, choices=ACCESS_CONTROLS, default=ACCESS_CONTROL_DENY)
    deploy: models.CharField(max_length=32, choices=ACCESS_CONTROLS, default=ACCESS_CONTROL_DENY)
    destination_commit: models.CharField(max_length=32, choices=ACCESS_CONTROLS, default=ACCESS_CONTROL_DENY)
    dry_run: models.CharField(max_length=32, choices=ACCESS_CONTROLS, default=ACCESS_CONTROL_DENY)
    group = models.ForeignKey("backend.Group", related_name="policies", on_delete=models.CASCADE)
    name = models.CharField(max_length=64, unique=True)
    no_push: models.CharField(max_length=32, choices=ACCESS_CONTROLS, default=ACCESS_CONTROL_DENY)
    uuid = models.UUIDField(default=uuid.uuid4)
    class Meta:
        unique_together = [["group_id", "name"]]