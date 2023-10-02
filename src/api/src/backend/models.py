from typing import Tuple
import uuid, re

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError

from backend.views.http.requests import (
    EnumContextType,
    EnumDestinationType,
    EnumRuntimeEnvironment,
    EnumTaskFlavor,
    EnumTaskType,
    EnumImageBuilder,
    EnumVisibility,
    EnumInstaller,
    EnumInvocationMode,
    EnumRetryPolicy,
    EnumDuplicateSubmissionPolicy,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MAX_TASK_EXEC_TIME,
    DEFAULT_MAX_WORKFLOW_EXEC_TIME
) 


ONE_HOUR_IN_SEC = 3600

TASK_INVOCATION_MODE_SYNC = "sync"
TASK_INVOCATION_MODE_ASYNC = "async"
TASK_INVOCATION_MODES = [
    (TASK_INVOCATION_MODE_SYNC, "sync"),
    (TASK_INVOCATION_MODE_ASYNC, "async")
]

TASK_TYPE_TEMPLATE = EnumTaskType.Template
TASK_TYPE_IMAGE_BUILD = EnumTaskType.ImageBuild
TASK_TYPE_APPLICATION = EnumTaskType.Application
TASK_TYPE_CONTAINER_RUN = EnumTaskType.ContainerRun  # Keep for backwards compatibility. container_run renamed to application
TASK_TYPE_REQUEST = EnumTaskType.Request
TASK_TYPE_FUNCTION = EnumTaskType.Function
TASK_TYPE_TAPIS_JOB = EnumTaskType.TapisJob
TASK_TYPE_TAPIS_ACTOR = EnumTaskType.TapisActor
TASK_TYPES = [
    (TASK_TYPE_TEMPLATE, EnumTaskType.Template),
    (TASK_TYPE_IMAGE_BUILD, EnumTaskType.ImageBuild),
    (TASK_TYPE_APPLICATION, EnumTaskType.Application),
    (TASK_TYPE_REQUEST, EnumTaskType.Request),
    (TASK_TYPE_FUNCTION, EnumTaskType.Function),
    (TASK_TYPE_TAPIS_JOB, EnumTaskType.TapisJob),
    (TASK_TYPE_TAPIS_ACTOR, EnumTaskType.TapisActor),
]

TASK_PROTOCOL_HTTP = "http"
TASK_PROTOCOL_SSH = "ssh"
TASK_PROTOCOL_SFTP = "sftp"
TASK_PROTOCOL_FTP = "ftp"
TASK_PROTOCOL_FTPS = "ftps"
TASK_PROTOCOLS = [
    (TASK_PROTOCOL_HTTP, "http"),
    (TASK_PROTOCOL_SSH, "ssh"),
    (TASK_PROTOCOL_SFTP, "sftp"),
    (TASK_PROTOCOL_FTP, "ftp"),
    (TASK_PROTOCOL_FTPS, "ftps"),
]

FUNCTION_TASK_RUNTIME_PYTHON39 = EnumRuntimeEnvironment.Python39
FUNCTION_TASK_RUNTIME_PYTHON_SINGULARITY = EnumRuntimeEnvironment.PythonSingularity
FUNCTION_TASK_RUNTIMES = [
    (FUNCTION_TASK_RUNTIME_PYTHON39, EnumRuntimeEnvironment.Python39),
    (FUNCTION_TASK_RUNTIME_PYTHON_SINGULARITY, EnumRuntimeEnvironment.PythonSingularity)
]

FUNCTION_TASK_INSTALLERS = [
    (EnumInstaller.Pip, EnumInstaller.Pip)
]

TASK_FLAVOR_C1_SML = EnumTaskFlavor.C1_SML
TASK_FLAVOR_C1_MED = EnumTaskFlavor.C1_MED
TASK_FLAVOR_C1_LRG = EnumTaskFlavor.C1_LRG
TASK_FLAVOR_C1_XLRG = EnumTaskFlavor.C1_XLRG
TASK_FLAVOR_C1_XXLRG = EnumTaskFlavor.C1_XXLRG
TASK_FLAVOR_G1_NVD_SML = EnumTaskFlavor.G1_NVD_SML
TASK_FLAVOR_G1_NVD_MED = EnumTaskFlavor.G1_NVD_MED
TASK_FLAVOR_G1_NVD_LRG = EnumTaskFlavor.G1_NVD_LRG

TASK_FLAVORS = [
    (TASK_FLAVOR_C1_SML, EnumTaskFlavor.C1_SML),
    (TASK_FLAVOR_C1_MED, EnumTaskFlavor.C1_MED),
    (TASK_FLAVOR_C1_LRG, EnumTaskFlavor.C1_LRG),
    (TASK_FLAVOR_C1_XLRG, EnumTaskFlavor.C1_XLRG),
    (TASK_FLAVOR_C1_XXLRG, EnumTaskFlavor.C1_XXLRG),
    (TASK_FLAVOR_G1_NVD_SML,  EnumTaskFlavor.G1_NVD_SML),
    (TASK_FLAVOR_G1_NVD_MED,  EnumTaskFlavor.G1_NVD_MED),
    (TASK_FLAVOR_G1_NVD_LRG, EnumTaskFlavor.G1_NVD_LRG)
]

ARCHIVE_TYPE_SYSTEM = "system"
ARCHIVE_TYPE_S3 = "s3"
ARCHIVE_TYPE_IRODS = "irods"
ARCHIVE_TYPES = [
    (ARCHIVE_TYPE_SYSTEM, "system"),
    (ARCHIVE_TYPE_S3, "s3"),
    (ARCHIVE_TYPE_IRODS, "irods")
]

IMAGE_BUILDER_KANIKO = EnumImageBuilder.Kaniko
IMAGE_BUILDER_SINGULARITY = EnumImageBuilder.Singularity
IMAGE_BUILDERS = [
    (IMAGE_BUILDER_KANIKO, EnumImageBuilder.Kaniko),
    (IMAGE_BUILDER_SINGULARITY, EnumImageBuilder.Singularity),
]

HTTP_METHOD_GET = "get"
HTTP_METHOD_POST = "post"
HTTP_METHOD_PUT = "put"
HTTP_METHOD_PATCH = "patch"
HTTP_METHOD_DELETE = "delete"
TASK_HTTP_METHODS = [
    (HTTP_METHOD_GET, "get"),
    (HTTP_METHOD_POST, "post"),
    (HTTP_METHOD_PUT, "put"),
    (HTTP_METHOD_PATCH, "patch"),
    (HTTP_METHOD_DELETE, "delete"),
]

CONTEXT_TYPE_GITHUB = EnumContextType.Github
CONTEXT_TYPE_GITLAB = EnumContextType.Gitlab
CONTEXT_TYPE_DOCKERHUB = EnumContextType.Dockerhub
CONTEXT_TYPES = [
    (CONTEXT_TYPE_GITHUB, EnumContextType.Github),
    (CONTEXT_TYPE_GITLAB, EnumContextType.Gitlab),
    (CONTEXT_TYPE_DOCKERHUB, EnumContextType.Dockerhub),
]

DESTINATION_TYPE_DOCKERHUB = EnumDestinationType.Dockerhub
DESTINATION_TYPE_DOCKERHUB_LOCAL = EnumDestinationType.DockerhubLocal
DESTINATION_TYPE_LOCAL = EnumDestinationType.Local
DESTINATION_TYPE_S3 = EnumDestinationType.Dockerhub
DESTINATION_TYPES = [
    (DESTINATION_TYPE_DOCKERHUB, EnumDestinationType.Dockerhub),
    (DESTINATION_TYPE_LOCAL, EnumDestinationType.Local)
    # TODO support s3 destinations
    # TODO support local destination
    # TODO support local dockerhub
]

IDENTITY_TYPES = CONTEXT_TYPES

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

RUN_STATUS_SUBMITTED = "submitted"
RUN_STATUS_PENDING = "pending"
RUN_STATUS_ACTIVE = "active"
RUN_STATUS_BACKOFF = "backoff"
RUN_STATUS_COMPLETED = "completed"
RUN_STATUS_FAILED = "failed"
RUN_STATUS_SUSPENDED = "suspended"
RUN_STATUS_ARCHIVING = "archiving"
RUN_STATUS_TERMINATED = "terminated"
RUN_STATUS_DEFERRED = "deferred"

RUN_STATUSES = [
    (RUN_STATUS_PENDING, "pending"),
    (RUN_STATUS_ACTIVE, "active"),
    (RUN_STATUS_BACKOFF, "backoff"),
    (RUN_STATUS_COMPLETED, "completed"),
    (RUN_STATUS_FAILED, "failed"),
    (RUN_STATUS_SUSPENDED, "suspended"),
    (RUN_STATUS_ARCHIVING, "archiving"),
    (RUN_STATUS_TERMINATED, "terminated"),
    (RUN_STATUS_SUBMITTED, "submitted"),
    (RUN_STATUS_DEFERRED, "deferred")
]

EXEC_STATUS_PENDING = "pending"
EXEC_STATUS_ACTIVE = "active"
EXEC_STATUS_BACKOFF = "backoff"
EXEC_STATUS_COMPLETED = "completed"
EXEC_STATUS_FAILED = "failed"
EXEC_STATUS_SUSPENDED = "suspended"
EXEC_STATUS_ARCHIVING = "archiving"
EXEC_STATUS_TERMINATED = "terminated"
EXEC_STATUS_SKIPPED = "skipped"

TASK_EXECUTION_STATUSES = EXEC_STATUSES = [
    (EXEC_STATUS_PENDING, "pending"),
    (EXEC_STATUS_ACTIVE, "active"),
    (EXEC_STATUS_BACKOFF, "backoff"),
    (EXEC_STATUS_COMPLETED, "completed"),
    (EXEC_STATUS_FAILED, "failed"),
    (EXEC_STATUS_SUSPENDED, "suspended"),
    (EXEC_STATUS_ARCHIVING, "archiving"),
    (EXEC_STATUS_TERMINATED, "terminated"),
    (EXEC_STATUS_SKIPPED, "skipped"),
]

DUPLICATE_SUBMISSION_POLICY_ALLOW = EnumDuplicateSubmissionPolicy.Allow
DUPLICATE_SUBMISSION_POLICY_DENY = EnumDuplicateSubmissionPolicy.Deny
DUPLICATE_SUBMISSION_POLICY_TERMINATE = EnumDuplicateSubmissionPolicy.Terminate
DUPLICATE_SUBMISSION_POLICY_DEFER = EnumDuplicateSubmissionPolicy.Defer
DUPLICATE_SUBMISSION_POLICIES = [
    (DUPLICATE_SUBMISSION_POLICY_ALLOW, EnumDuplicateSubmissionPolicy.Allow),
    (DUPLICATE_SUBMISSION_POLICY_DENY, EnumDuplicateSubmissionPolicy.Deny),
    (DUPLICATE_SUBMISSION_POLICY_TERMINATE, EnumDuplicateSubmissionPolicy.Terminate),
    (DUPLICATE_SUBMISSION_POLICY_DEFER, EnumDuplicateSubmissionPolicy.Defer)
]

VISIBILITY_PUBLIC = EnumVisibility.Public
VISIBILITY_PRIVATE = EnumVisibility.Private
VISIBILITY_TYPES = [
    (VISIBILITY_PUBLIC, EnumVisibility.Public),
    (VISIBILITY_PRIVATE, EnumVisibility.Private)
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
    branch = models.CharField(max_length=255, null=True)
    commit = models.TextField(max_length=255, null=True)
    commit_sha = models.CharField(max_length=128, null=True)
    context_url = models.CharField(max_length=128, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    cron = models.CharField(null=True, max_length=128)
    directives = models.JSONField(null=True)
    group = models.ForeignKey("backend.Group", related_name="events", null=True, on_delete=models.CASCADE)
    message = models.TextField()
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
    env = models.JSONField(null=True)
    params = models.JSONField(null=True)
    group = models.ForeignKey("backend.Group", related_name="pipelines", on_delete=models.CASCADE)
    invocation_mode = models.CharField(max_length=16, default=EnumInvocationMode.Async)
    max_exec_time = models.BigIntegerField(
        default=DEFAULT_MAX_WORKFLOW_EXEC_TIME,
        validators=[MaxValueValidator(DEFAULT_MAX_WORKFLOW_EXEC_TIME), MinValueValidator(1)]
    )
    max_retries = models.IntegerField(default=DEFAULT_MAX_RETRIES)
    duplicate_submission_policy = models.CharField(max_length=32, choices=DUPLICATE_SUBMISSION_POLICIES, default=EnumDuplicateSubmissionPolicy.Terminate)
    owner = models.CharField(max_length=64)
    retry_policy = models.CharField(max_length=32, default=EnumRetryPolicy.ExponentialBackoff)
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
    last_modified = models.DateTimeField(null=True)
    logs = models.TextField(null=True)
    pipeline = models.ForeignKey("backend.Pipeline", related_name="runs", on_delete=models.CASCADE)
    status = models.CharField(max_length=16, choices=RUN_STATUSES, default=RUN_STATUS_SUBMITTED)
    started_at = models.DateTimeField(null=True)
    uuid = models.UUIDField(primary_key=True)

class Task(models.Model):
    class Meta:
            constraints = [
                models.UniqueConstraint(
                    fields=["id", "pipeline_id"],
                    name="task_id_pipeline_id"
                )
            ]
            indexes = [
                models.Index(fields=["id", "pipeline_id"])
            ]

    # Props
    id = models.CharField(validators=[validate_id], max_length=128)
    cache = models.BooleanField(null=True)
    depends_on = models.JSONField(null=True, default=list)
    description = models.TextField(null=True)
    flavor = models.CharField(max_length=32, choices=TASK_FLAVORS, default=TASK_FLAVOR_C1_MED)
    input = models.JSONField(null=True)
    invocation_mode = models.CharField(max_length=16, default=EnumInvocationMode.Async)
    max_exec_time = models.BigIntegerField(
        default=DEFAULT_MAX_TASK_EXEC_TIME,
        validators=[MaxValueValidator(DEFAULT_MAX_TASK_EXEC_TIME*3), MinValueValidator(1)]
    )
    max_retries = models.IntegerField(default=DEFAULT_MAX_RETRIES)
    output = models.JSONField(null=True)
    pipeline = models.ForeignKey("backend.Pipeline", related_name="tasks", on_delete=models.CASCADE)
    poll = models.BooleanField(null=True)
    retry_policy = models.CharField(max_length=32, default=EnumRetryPolicy.ExponentialBackoff)
    type = models.CharField(max_length=32, choices=TASK_TYPES)
    uses = models.JSONField(null=True)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # Image build specific properties
    builder = models.CharField(max_length=32, choices=IMAGE_BUILDERS, null=True)
    context = models.OneToOneField("backend.Context", null=True, on_delete=models.CASCADE)
    destination = models.OneToOneField("backend.Destination", null=True, on_delete=models.CASCADE)
    
    # Request specific properties
    auth = models.ForeignKey("backend.Credentials", null=True, on_delete=models.CASCADE)
    data = models.JSONField(null=True)
    headers = models.JSONField(null=True)
    http_method = models.CharField(max_length=32, choices=TASK_HTTP_METHODS, null=True)
    protocol = models.CharField(max_length=32, choices=TASK_PROTOCOLS, null=True)
    query_params = models.JSONField(null=True)
    url = models.CharField(max_length=255, null=True)

    # Function specific properties
    git_repositories = models.JSONField(null=True, default=list)
    runtime = models.CharField(max_length=64, null=True)
    code = models.TextField(null=True)
    command = models.TextField(null=True)
    installer = models.CharField(max_length=64, null=True)
    packages = models.JSONField(null=True, default=list)

    # Container run specific properties
    # Full image name for container run. includes scheme.
    image = models.CharField(max_length=128, null=True)

    # Tapis job specific properties
    tapis_job_def = models.JSONField(null=True)

    # Tapis actor specific properties
    tapis_actor_id = models.CharField(max_length=128, null=True)
    tapis_actor_message = models.TextField(null=True)

    def clean(self):
        errors = {}
        
        # Validate runtimes
        (success, error) = self.validate_function_task_installers()
        if not success: errors = {**errors, "invalid-runtime-installer": error}

        # Validate packages schema
        (success, error) = self.validate_packages_schema()
        if not success: errors = {**errors, "packages-schema-error": error}

        if errors:
            raise ValidationError(errors)

    def validate_function_task_installers(self) -> Tuple[bool, str]:
        installer_runtime_mapping = {
            FUNCTION_TASK_RUNTIME_PYTHON39: [EnumInstaller.Pip],
            FUNCTION_TASK_RUNTIME_PYTHON_SINGULARITY: [EnumInstaller.Pip]
        }

        installers_for_runtime = installer_runtime_mapping.get(self.runtime, None)
        if installers_for_runtime == None: return (False, f"Invalid runtime '{self.runtime}'")
        if self.installer not in installers_for_runtime:
            return (False, f"Installer '{self.installer}' for runtime {self.runtime}")

    def validate_packages_schema(self) -> Tuple[bool, str]:
        if type(self.packages) != list:
            return (False, f"Invalid installer: Installer '{self.installer}' for runtime {self.runtime}")
        
        for package in self.packages:
            if type(package) != str: return (False, "Items in the package array must be strings")

    def validate_input(self):
        pass

    def validate_output(self):
        pass


class TaskExecution(models.Model):
    last_modified = models.DateTimeField(null=True)
    last_message = models.TextField(null=True)
    pipeline_run = models.ForeignKey("backend.PipelineRun", related_name="task_executions", on_delete=models.CASCADE)
    started_at = models.DateTimeField(null=True)
    stdout = models.TextField(null=True)
    stderr = models.TextField(null=True)
    status = models.CharField(max_length=16, choices=TASK_EXECUTION_STATUSES, default=RUN_STATUS_PENDING)
    task = models.ForeignKey("backend.Task", related_name="task_executions", on_delete=models.CASCADE)
    uuid = models.UUIDField(primary_key=True)