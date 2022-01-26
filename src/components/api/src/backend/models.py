import uuid

from django.db import models

CREDENTIAL_TYPE_IMAGE_REGISTRY = "I"
CREDENTIAL_TYPE_REPOSITORY = "R"
CREDENTIAL_TYPE_API = "A"
CREDENTIAL_TYPES = [
    (CREDENTIAL_TYPE_IMAGE_REGISTRY, "image_registry"),
    (CREDENTIAL_TYPE_REPOSITORY, "repository"),
    (CREDENTIAL_TYPE_API, "api"),
]

EVENT_PUSH = "P"
EVENT_MERGE_REQUEST_EVENT = "M"
EVENT_TYPES = [
    (EVENT_PUSH, "push"),
    (EVENT_MERGE_REQUEST_EVENT, "merge_request_event"),
]

POLICY_TYPE_GROUP = "G"
POLICY_TYPE_USER = "U"
POLICY_TYPES = [
    (POLICY_TYPE_GROUP, "group"),
    (POLICY_TYPE_USER, "user"),
]

READ = "R"
WRITE = "W"
MODIFY = "M"
PERMISSIONS = [
    (READ, "read"),
    (WRITE, "write"), # Write implies read
    (MODIFY, "modify"), # Modify implies write which implies read
]

ALLOW = True
DENY = False
ACCESS_CONTROLS = [
    (ALLOW, "allow"),
    (DENY, "deny")
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

class Build(models.Model):
    status = models.PositiveSmallIntegerField(choices=STATUSES, default=STATUS_QUEUED)
    event = models.ForeignKey("backend.Event", on_delete=models.PROTECT)
    deployment = models.ForeignKey("backend.Deployment", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Credential(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    description = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Deployment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auto_deploy = models.BooleanField(default=False, null=False)
    auto_deploy = models.BooleanField(default=False, null=False)
    branch = models.CharField(max_length=255, null=False)
    context = models.CharField(max_length=64, null=False)
    deployment_credentials = models.ForeignKey("backend.DeploymentCredential", on_delete=models.PROTECT)
    deployment_policies = models.ForeignKey("backend.DeploymentPolicy", on_delete=models.PROTECT)
    destination = models.CharField(max_length=128)
    dockerfile_path = models.CharField(max_length=255, default="/")
    event_type = models.CharField(max_length=1, choices=EVENT_TYPES, null=True)
    image_tag = models.CharField(max_length=64, null=True)
    name = models.CharField(max_length=128)
    owner = models.CharField(max_length=32)
    repository_url = models.CharField(max_length=255)
    user = models.CharField(max_length=255, null=True)
    class Meta:
        unique_together = [["destination", "image_tag"]]

class DeploymentCredential(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deployment_id = models.UUIDField(editable=False, null=False)
    credential = models.ForeignKey("backend.Credential", on_delete=models.PROTECT)
    type = models.CharField(max_length=1, choices=CREDENTIAL_TYPES, null=False)

class DeploymentPolicy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deployment_id = models.UUIDField(editable=False, null=False)
    policy = models.ForeignKey("backend.Policy", on_delete=models.PROTECT)
    policy_type = models.CharField(max_length=1, choices=POLICY_TYPES, null=False)
    policy_type_value = models.CharField(max_length=128, null=False)

class Group(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)

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
    deploy: models.BooleanField(choices=ACCESS_CONTROLS, default=DENY, null=False)
    custom_tag: models.BooleanField(choices=ACCESS_CONTROLS, default=DENY, null=False)
    tag_commit_sha: models.BooleanField(choices=ACCESS_CONTROLS, default=DENY, null=False)
    no_push: models.BooleanField(choices=ACCESS_CONTROLS, default=DENY, null=False)
    dry_run: models.BooleanField(choices=ACCESS_CONTROLS, default=DENY, null=False)
    policies: models.CharField(choices=PERMISSIONS, null=True)
    credentials: models.CharField(choices=PERMISSIONS, null=True)
    deployments: models.CharField(choices=PERMISSIONS, null=True)
    groups: models.CharField(choices=PERMISSIONS, null=True)
    group_users: models.CharField(choices=PERMISSIONS, null=True)