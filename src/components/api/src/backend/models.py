import uuid

from django.db import models

ACTION_WEBHOOK = "W"
ACTIONS = [
    (ACTION_WEBHOOK, "webhook"),
]

CONTEXT_TYPE_GITHUB = 0
CONTEXT_TYPE_GITLAB = 1
CONTEXT_TYPES = [
    (CONTEXT_TYPE_GITHUB, "github"),
    (CONTEXT_TYPE_GITLAB, "gitlab"),
]

EVENT_PUSH = "P"
EVENT_MERGE_REQUEST_EVENT = "M"
EVENT_TYPES = [
    (EVENT_PUSH, "push"),
    (EVENT_MERGE_REQUEST_EVENT, "merge_request_event"),
]

GROUP_STATUS_DISABLED = 0
GROUP_STATUS_ENABLED = 1
GROUP_STATUSES = [
    (GROUP_STATUS_DISABLED, "disabled"),
    (GROUP_STATUS_ENABLED, "enabled")
]

READ = "R"
WRITE = "W"
MODIFY = "M"
PERMISSIONS = [
    (READ, "read"),
    (WRITE, "write"), # Write implies read
    (MODIFY, "modify"), # Modify implies write which implies read
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

REPOSITORY_GITHUB = 0
REPOSITORY_GITLAB = 1
REPOSITORIES = [
    ( REPOSITORY_GITHUB, "github.com" ),
    ( REPOSITORY_GITLAB, "gitlab.com" ),
]

DESTINATION_TYPE_REGISTRY = 0
DESTINATION_TYPES = [
    ( DESTINATION_TYPE_REGISTRY, "dockerhub" )
    # NOTE support s3 destinations?
]

class Build(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.PositiveSmallIntegerField(choices=STATUSES, default=STATUS_QUEUED)
    event = models.ForeignKey("backend.Event", on_delete=models.PROTECT)
    deployment = models.ForeignKey("backend.Deployment", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Credential(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.TextField(null=True)
    group = models.ForeignKey("backend.Group", on_delete=models.PROTECT)
    name = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Context(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    credential = models.ForeignKey(
        "backend.Credential", default=None, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=64, null=False)
    type = models.PositiveSmallIntegerField(choices=REPOSITORIES, null=False)
    repo = models.CharField(max_length=255, null=False)
    visibility = models.PositiveSmallIntegerField(choices=VISIBILITY_TYPES, null=False)

class Deployment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auto_deploy = models.BooleanField(default=False, null=False)
    auto_deploy = models.BooleanField(default=False, null=False)
    branch = models.CharField(max_length=255, null=False)
    context = models.ForeignKey("backend.Context", on_delete=models.PROTECT)
    deployment_policies = models.ForeignKey("backend.DeploymentPolicy", on_delete=models.PROTECT)
    destination = models.ForeignKey("backend.Destination", on_delete=models.PROTECT)
    dockerfile_path = models.CharField(max_length=255, default="/")
    event_type = models.CharField(max_length=1, choices=EVENT_TYPES, null=True)
    group = models.ForeignKey("backend.Group", on_delete=models.PROTECT)
    image_tag = models.CharField(max_length=64, null=True)
    name = models.CharField(max_length=128)
    owner = models.CharField(max_length=32)

class Destination(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey("backend.Group", on_delete=models.PROTECT)
    credential = models.ForeignKey(
        "backend.Credential", default=None, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=64, null=False)
    type = models.SmallIntegerField(choices=DESTINATION_TYPES, null=False)
    url = models.CharField(max_length=255)
    tag = models.CharField(max_length=128)

class DeploymentPolicy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deployment_id = models.UUIDField(editable=False, null=False)
    policy = models.ForeignKey("backend.Policy", on_delete=models.PROTECT)
    group = models.ForeignKey("backend.Group", on_delete=models.PROTECT)

class Group(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, unique=True)
    owner = models.CharField(max_length=64)
    users = models.ForeignKey("backend.GroupUser", on_delete=models.PROTECT)

class GroupUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group_id = models.UUIDField(editable=False, null=False)
    username = models.CharField(max_length=128)
    class Meta:
        unique_together = [["group_id", "username"]]

class Event(models.Model):
    source = models.CharField(max_length=255)
    branch = models.CharField(max_length=255)
    user = models.CharField(max_length=255)
    commit_sha = models.CharField(max_length=128)
    commit = models.TextField(max_length=1024, null=True)
    event_type = models.CharField(max_length=1, choices=EVENT_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

class Policy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, unique=True)
    deploy: models.BooleanField(choices=ACCESS_CONTROLS, default=ACCESS_CONTROL_DENY, null=False)
    custom_tag: models.BooleanField(choices=ACCESS_CONTROLS, default=ACCESS_CONTROL_DENY, null=False)
    tag_commit_sha: models.BooleanField(choices=ACCESS_CONTROLS, default=ACCESS_CONTROL_DENY, null=False)
    no_push: models.BooleanField(choices=ACCESS_CONTROLS, default=ACCESS_CONTROL_DENY, null=False)
    dry_run: models.BooleanField(choices=ACCESS_CONTROLS, default=ACCESS_CONTROL_DENY, null=False)
    credentials: models.CharField(choices=PERMISSIONS, null=True)