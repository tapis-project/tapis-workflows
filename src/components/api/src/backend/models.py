import uuid

from django.db import models
from django.contrib.auth.models import User

ACTION_TYPE_CONTAINER_BUILD = 0
ACTION_TYPE_CONTAINER_EXEC = 1
ACTION_TYPE_CONTAINER_WEBHOOK = 2
ACTION_TYPES = [
    (ACTION_TYPE_CONTAINER_BUILD, "container_build"),
    (ACTION_TYPE_CONTAINER_EXEC, "container_exec"),
    (ACTION_TYPE_CONTAINER_WEBHOOK, "webhook_notification"),
]

# ACTION_STAGE_PRE_BUILD = 0
ACTION_STAGE_BUILD = 1
ACTION_STAGE_POST_BUILD = 2
ACTION_STAGE_TYPES = [
    # TODO Support
    # (ACTION_STAGE_PRE_BUILD, "pre_build"),
    (ACTION_STAGE_BUILD, "build"),
    (ACTION_STAGE_POST_BUILD, "post_build"),
]

HTTP_METHOD_GET = 0
HTTP_METHOD_POST = 1
HTTP_METHOD_PUT = 2
HTTP_METHOD_PATCH = 3
HTTP_METHOD_DELETE = 4
ACTION_HTTP_METHODS = [
    (HTTP_METHOD_GET, "get"),
    (HTTP_METHOD_POST, "post"),
    (HTTP_METHOD_PUT, "put"),
    (HTTP_METHOD_PATCH, "patch"),
    (HTTP_METHOD_DELETE, "delete"),
]

CONTEXT_TYPE_GITHUB = 0
CONTEXT_TYPE_GITLAB = 1
CONTEXT_TYPES = [
    (CONTEXT_TYPE_GITHUB, "github"),
    (CONTEXT_TYPE_GITLAB, "gitlab"),
]

DESTINATION_TYPE_REGISTRY = 0
DESTINATION_TYPES = [
    ( DESTINATION_TYPE_REGISTRY, "dockerhub" )
    # NOTE support s3 destinations?
]

GROUP_STATUS_DISABLED = 0
GROUP_STATUS_ENABLED = 1
GROUP_STATUSES = [
    (GROUP_STATUS_DISABLED, "disabled"),
    (GROUP_STATUS_ENABLED, "enabled")
]

PERMISSION_READ = "R"
PERMISSION_WRITE = "W"
PERMISSION_MODIFY = "M"
PERMISSIONS = [
    (PERMISSION_READ, "read"),
    (PERMISSION_WRITE, "write"), # Write implies read
    (PERMISSION_MODIFY, "modify"), # Modify implies write which implies read
]

ACCESS_CONTROL_ALLOW = True
ACCESS_CONTROL_DENY = False
ACCESS_CONTROLS = [
    (ACCESS_CONTROL_ALLOW, "allow"),
    (ACCESS_CONTROL_DENY, "deny")
]

STATUS_QUEUED = 0
STATUS_IN_PROGRESS = 1
STATUS_PUSHING = 2
STATUS_FAILED = 3
STATUS_SUCCESS = 4
STATUSES = [
    ( STATUS_QUEUED, "queued" ),
    ( STATUS_IN_PROGRESS, "in_progress" ),
    ( STATUS_PUSHING, "pushing" ),
    ( STATUS_FAILED, "failed" ),
    ( STATUS_SUCCESS, "success" ),
]

VISIBILITY_PUBLIC = 0
VISIBILITY_PRIVATE = 1
VISIBILITY_TYPES = [
    ( VISIBILITY_PUBLIC, "public" ),
    ( VISIBILITY_PRIVATE, "private" )
]

class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

class Action(models.Model):
    description = models.TextField(null=True)
    pipeline = models.ForeignKey("backend.Pipeline", related_name="actions", on_delete=models.CASCADE)
    type = models.PositiveSmallIntegerField(choices=ACTION_TYPES)
    http_method = models.PositiveSmallIntegerField(choices=ACTION_HTTP_METHODS, null=True)
    name = models.CharField(max_length=128)
    stage = models.PositiveSmallIntegerField(choices=ACTION_STAGE_TYPES)
    url = models.CharField(max_length=255, null=True)
    uuid = models.UUIDField(default=uuid.uuid4)
    class Meta:
        unique_together = [["name", "pipeline_id"]]

class Aliases(models.Model):
    type = models.PositiveSmallIntegerField(choices=CONTEXT_TYPES)
    account = models.ForeignKey("backend.Account", related_name="aliases", on_delete=models.CASCADE)
    group = models.ForeignKey("backend.Group", related_name="aliases", on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4)
    value = models.CharField(max_length=128)
    class Meta:
        unique_together = [["account_id", "value", "type"]]

class Build(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    event = models.OneToOneField("backend.Event", on_delete=models.PROTECT)
    group = models.ForeignKey("backend.Group", related_name="builds", on_delete=models.PROTECT)
    pipeline = models.ForeignKey("backend.Pipeline", related_name="builds", on_delete=models.PROTECT)
    status = models.PositiveSmallIntegerField(choices=STATUSES, default=STATUS_QUEUED)
    updated_at = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(default=uuid.uuid4)

class Credential(models.Model):
    id = models.CharField(primary_key=True, max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(null=True)
    group = models.ForeignKey("backend.Group", on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4)
    class Meta:
        unique_together = [["id", "group_id"]]

class Context(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    credential = models.OneToOneField("backend.Credential", null=True, on_delete=models.PROTECT)
    action = models.ForeignKey("backend.Action", related_name="context", on_delete=models.CASCADE)
    branch = models.CharField(max_length=128)
    group = models.ForeignKey("backend.Group", on_delete=models.CASCADE)
    repo = models.CharField(max_length=255)
    type = models.PositiveSmallIntegerField(choices=CONTEXT_TYPES)
    visibility = models.PositiveSmallIntegerField(choices=VISIBILITY_TYPES)
    uuiid = models.UUIDField(default=uuid.uuid4)

class Destination(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    action = models.ForeignKey("backend.Action", related_name="destination", on_delete=models.CASCADE)
    credential = models.OneToOneField("backend.Credential", on_delete=models.PROTECT)
    group = models.ForeignKey("backend.Group", on_delete=models.CASCADE)
    tag = models.CharField(max_length=128)
    type = models.SmallIntegerField(choices=DESTINATION_TYPES)
    url = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid.uuid4)

class Pipeline(models.Model):
    id = models.CharField(primary_key=True, max_length=128)
    auto_build = models.BooleanField(default=False)
    branch = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    source = models.PositiveSmallIntegerField(choices=CONTEXT_TYPES)
    dockerfile_path = models.CharField(max_length=255, default="/")
    group = models.ForeignKey("backend.Group", on_delete=models.CASCADE)
    image_tag = models.CharField(max_length=64, null=True)
    owner = models.CharField(max_length=64)
    uuid = models.UUIDField(default=uuid.uuid4)

class Group(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=128, unique=True)
    owner = models.CharField(max_length=64)
    uuid = models.UUIDField(default=uuid.uuid4)
    indexes = [
        models.Index(fields=["name", "owner"])
    ]

class Event(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    branch = models.CharField(max_length=255)
    commit = models.TextField(null=True)
    commit_sha = models.CharField(max_length=128)
    source = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid.uuid4)

class Policy(models.Model):      
    context_commit: models.BooleanField(choices=ACCESS_CONTROLS, default=ACCESS_CONTROL_DENY)
    credentials: models.CharField(choices=PERMISSIONS, null=True)
    custom_tag: models.BooleanField(choices=ACCESS_CONTROLS, default=ACCESS_CONTROL_DENY)
    deploy: models.BooleanField(choices=ACCESS_CONTROLS, default=ACCESS_CONTROL_DENY)
    destination_commit: models.BooleanField(choices=ACCESS_CONTROLS, default=ACCESS_CONTROL_DENY)
    dry_run: models.BooleanField(choices=ACCESS_CONTROLS, default=ACCESS_CONTROL_DENY)
    group = models.ForeignKey("backend.Group", related_name="policies", on_delete=models.CASCADE)
    name = models.CharField(max_length=64, unique=True)
    no_push: models.BooleanField(choices=ACCESS_CONTROLS, default=ACCESS_CONTROL_DENY)
    uuid = models.UUIDField(default=uuid.uuid4)
    class Meta:
        unique_together = [["group_id", "name"]]