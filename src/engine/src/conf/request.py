import re

from enum import Enum, EnumMeta
from typing import List, Literal, Union, Dict, TypedDict
from typing_extensions import Annotated
from pydantic import BaseModel, validator, root_validator, Field, Extra

### Enums ###
class _EnumMeta(EnumMeta):  
    def __contains__(cls, item): 
        try:
            cls(item)
        except ValueError:
            return False
        else:
            return True

class EnumArchiveType(str, Enum, metaclass=_EnumMeta):
    Irods = "irods"
    S3 = "s3"
    System = "system"

class EnumContextType(str, Enum, metaclass=_EnumMeta):
    Github = "github"
    Gitlab = "gitlab"
    Dockerhub = "dockerhub"

class EnumDestinationType(str, Enum, metaclass=_EnumMeta):
    Dockerhub = "dockerhub"
    DockerhubLocal = "dockerhub_local"
    Local = "local"
    S3 = "s3"

class EnumDuplicateSubmissionPolicy(str, Enum, metaclass=_EnumMeta):
    Allow = "allow",
    Deny = "deny"
    Terminate = "terminate"
    Defer = "defer"

class EnumImageBuilder(str, Enum, metaclass=_EnumMeta):
    Kaniko = "kaniko"
    Singularity = "singularity"

class EnumRuntimeEnvironment(str, Enum, metaclass=_EnumMeta):
    Python39 = "python:3.9"
    PythonSingularity = "tapis/workflows-python-singularity:0.1.0"

class EnumInstaller(str, Enum, metaclass=_EnumMeta):
    Pip = "pip"

class EnumPipelineType(str, Enum, metaclass=_EnumMeta):
    Workflow = "workflow"
    CI = "ci"

class EnumValueType(str, Enum, metaclass=_EnumMeta):
    String = "string"
    Number = "number"
    Boolean = "boolean"

class EnumRetryPolicy(str, Enum, metaclass=_EnumMeta):
    ExponentialBackoff = "exponential_backoff"

class EnumInvocationMode(str, Enum, metaclass=_EnumMeta):
    Async = "async"
    Sync = "sync"

class EnumTaskIOTypes(str, Enum, metaclass=_EnumMeta):
    String = "string"
    Number = "number"
    Boolean = "boolean"
    StringArray = "string_array"
    NumberArray = "number_array"
    BooleanArray = "boolean_array"
    MixedArray = "mixed_array"
    TapisFileInput = "tapis_file_input"
    TapisFileInputArray = "tapis_file_input_array"

class EnumTaskInputValueFromKey(str, Enum, metaclass=_EnumMeta):
    Env = "env"
    Params = "params"
    TaskOutput = "task_output"

class EnumTaskFlavor(str, Enum, metaclass=_EnumMeta):
    C1_SML = "c1sml"
    C1_MED = "c1med"
    C1_LRG = "c1lrg"
    C1_XLRG = "c1xlrg"
    C1_XXLRG = "c1xxlrg"
    G1_NVD_SML = "g1nvdsml"
    G1_NVD_MED = "g1nvdmed"
    G1_NVD_LRG = "g1nvdlrg"

class EnumTaskType(str, Enum, metaclass=_EnumMeta):
    ImageBuild = "image_build"
    Request = "request"
    Function = "function"
    ContainerRun = "container_run"
    Application = "application"
    TapisActor = "tapis_actor"
    TapisJob = "tapis_job"

class EnumVisibility(str, Enum, metaclass=_EnumMeta):
    Private = "private"
    Public = "public"
############

### Defaults ###
DEFAULT_MAX_RETRIES = 0
DEFAULT_MAX_EXEC_TIME = 3600 # in seconds
DEFAULT_MAX_TASK_EXEC_TIME = DEFAULT_MAX_EXEC_TIME
DEFAULT_MAX_WORKFLOW_EXEC_TIME = DEFAULT_MAX_EXEC_TIME*3
DEFAULT_ARCHIVE_DIR = "/workflows/archive/"
################

### Validators ###
def validate_id(value):
    pattern = re.compile(r"^[A-Z0-9\-_]+$")
    if pattern.match(value) == None:
        raise ValueError("`id` property must only contain alphanumeric characters, underscores, and hypens")

    return value

def validate_ctx_dest_url(value):
    pattern = re.compile(r"^[a-zA-Z0-9-_]+/[a-zA-Z0-9-_]+$")
    if pattern.match(value) == None:
        raise ValueError("`url` must follow the format:  `<username>/<name>`")

    return value

################## Common ####################
class ID(str):
    _id_regex = re.compile(r"^[a-zA-Z0-9]+[a-zA-Z0-9\-_]*$")
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(
            pattern=cls._id_regex,
            examples=['task_id', 'Task_ID', '0123-task-id'],
        )
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str) and not isinstance(v, int):
            raise TypeError("Invalid 'id' format. Must start with alphanumeric chars followed by 0 or more alphanumeric chars, '_', and '-'")
        match = cls._id_regex.fullmatch(v)
        if not match:
            raise ValueError("Invalid 'id' format. Must start with alphanumeric chars followed by 0 or more alphanumeric chars, '_', and '-'")
        return v

class Value(BaseModel):
    type: EnumValueType = EnumValueType.String
    value: Union[str, int, float, bool] = None
    value_from: Dict[str, str] = None

    @root_validator(pre=True)
    def value_or_value_from(cls, values):
        # Either 'value' or 'value_from' must be set on every variable
        if (
            values.get("value", None) == None
            and values.get("value_from", None) == None
        ):
            raise ValueError(
                "Missing 'value' or 'value_from' property in variable values")

        return values

    @validator("value", pre=True)
    def value_type_validation(cls, value):
        if type(value) not in [str, bool, int, float]:
            raise TypeError("Variable values must be a string, number, or boolean'")

        return value

    @validator("value_from", pre=True)
    def value_from_type_validation(cls, value):
        is_dict = type(value) == dict
        is_valid = len([k for k in value if (type(k) == str and type(value[k]) == str)]) < 1
        if (not is_dict or (is_dict and is_valid)):
            raise TypeError(
                "The value of a Value object's 'value_from' property must be a single key-value pair where both the key and the value are non-empty strings")
        return value

Key = str

class ValueWithRequirements(Value):
    required: bool = False

KeyVal = Dict[Key, Value]
Params  = Dict[Key, ValueWithRequirements]
################## /Common ###################

class S3Credentials(TypedDict):
    access_key: str
    access_secret: str

class IRODSCredentials(TypedDict):
    user: str
    password: str

# Archive
class BaseArchive(BaseModel):
    id: ID
    credentials: Union[
        S3Credentials,
        IRODSCredentials
    ] = None
    identity_uuid: str = None
    type: EnumArchiveType

    # System archive
    system_id: str = None
    archive_dir: str = None

    # S3 archive
    endpoint: str = None
    bucket: str = None
    # encrypt: bool = None
    # secure: bool = None
    region: str = None

    # IRODS archive
    host: str = None
    port: str = None

class SystemArchive(BaseArchive):
    system_id: str
    archive_dir: str = DEFAULT_ARCHIVE_DIR # Relative to the system's RootDir

class S3Archive(BaseArchive):
    credentials: S3Credentials = None
    identity_uuid: str = None
    endpoint: str
    bucket: str
    region: str

    @root_validator
    def validate_supported_types(cls, values):
        creds = values.get("credentials")
        identity_uuid = values.get("identity_uuid")

        if creds == None and identity_uuid == None:
            raise ValueError("Archive of type `s3` must provide either an identity_uuid or credentials")

        return values

class AddRemoveArchive(BaseModel):
    archive_id: str

class IRODSArchive(BaseArchive):
    credentials: S3Credentials = None
    identity_uuid: str = None
    host: str
    port: str

    @root_validator
    def validate_supported_types(cls, values):
        creds = values.get("credentials")
        identity_uuid = values.get("identity_uuid")

        if creds == None and identity_uuid == None:
            raise ValueError("Archive of type `irods` must provide either an identity_uuid or credentials")

        return values

# Auth
class AuthRequest(BaseModel):
    username: str
    password: str

# Identities
class GithubCredentials(TypedDict):
    username: str
    personal_access_token: str

class DockerhubCredentials(TypedDict):
    username: str
    token: str

class IdentityCreateRequest(BaseModel):
    type: str
    name: str
    description: str = None
    credentials: Union[
        GithubCredentials,
        DockerhubCredentials
    ]

# ContextCredentialTypes = Union[GithubCredentials, SomethingElse]
ContextCredentialTypes = Union[GithubCredentials, DockerhubCredentials]

class Context(BaseModel):
    credentials: ContextCredentialTypes = None
    branch: str = None
    build_file_path: str = None
    identity_uuid: str = None
    sub_path: str = None
    tag: str = None
    type: EnumContextType
    url: str
    visibility: str

    # Validators
    # _validate_url = validator("url", allow_reuse=True)(validate_ctx_dest_url)

# TODO add more types to the destination credential types as they become supported
DestinationCredentialTypes = DockerhubCredentials

class Destination(BaseModel):
    type: EnumDestinationType
    tag: str = None
    credentials: DestinationCredentialTypes = None
    identity_uuid: str = None

class RegistryDestination(Destination):
    tag: str = None
    credentials: DestinationCredentialTypes = None
    identity_uuid: str = None
    url: str

    # Validators
    # _validate_url = validator("url", allow_reuse=True)(validate_ctx_dest_url)

    @root_validator
    def creds_or_identity(csl, values):
        creds, identity = values.get("credentials"), values.get("identity_uuid")
        if creds == None and identity == None:
            raise ValueError("Missing credentials and identity_uuid. Must provide at lease one.")

        return values

class LocalDestination(Destination):
    filename: str = None

# Events
class BaseEvent(BaseModel):
    branch: str = None
    directives: str = None
    commit: str = None
    commit_sha: str = None
    context_url: str = None
    pipeline_id: str = None
    source: str = None
    username: str = None

class APIEvent(BaseEvent):
    params: KeyVal = {}
    directives: List[str] = None

class WebhookEvent(BaseEvent):
    branch: str
    commit: str
    commit_sha: str
    source: str
    context_url: str
    username: str
    tenant_id: str

# Groups and Users
class GroupUserReq(BaseModel):
    username: str
    is_admin: bool = False

GroupUserCreateRequest = GroupUserReq

class GroupUserPutPatchRequest(BaseModel):
    is_admin: bool

class GroupCreateRequest(BaseModel):
    id: ID
    users: List[GroupUserReq] = []

    # Validators
    # _validate_id = validator("id", allow_reuse=True)(validate_id) 

class TaskDependency(BaseModel):
    id: ID
    can_fail: bool = False

    # Validators
    # _validate_id = validator("id", allow_reuse=True)(validate_id)

# Task I/O Types ---------------------------------------------------------

class TaskOutputRef(BaseModel):
    task_id: str
    output_id: str

# Input -----------------------------------------------------------------

class BaseInputValue(BaseModel):
    type: EnumTaskIOTypes
    value: Union[str, int, float, bytes] = None
    value_from: Union[
        Dict[
            Union[
                EnumTaskInputValueFromKey.Env,
                EnumTaskInputValueFromKey.Params,
            ],
            str
        ],
        Dict[EnumTaskInputValueFromKey.TaskOutput, TaskOutputRef]
    ] = None

Input = Dict # TODO move validation logic to pydantic model

# Output -----------------------------------------------------------------

class BaseOutputValue(BaseModel):
    type: EnumTaskIOTypes
    value: Union[str, int, float, bytes]

Output = Dict[str, BaseOutputValue]

# ------------------------------------------------------------------------

class HTTPBasicAuthCreds(BaseModel):
    username: str = None
    password: str = None

class Auth(BaseModel):
    type: str = "http_basic_auth"
    creds: HTTPBasicAuthCreds

class ExecutionProfile(BaseModel):
    max_exec_time: int = DEFAULT_MAX_EXEC_TIME
    invocation_mode: str = EnumInvocationMode.Async
    retry_policy: str = EnumRetryPolicy.ExponentialBackoff
    max_retries: int = DEFAULT_MAX_RETRIES
    duplicate_submission_policy: str = EnumDuplicateSubmissionPolicy.Terminate

class TaskExecutionProfile(ExecutionProfile):
    flavor: EnumTaskFlavor = EnumTaskFlavor.C1_MED
    duplicate_submission_policy = None

class GitRepository(BaseModel):
    url: str
    branch: str = None # If no branch specified, the default branch will be used
    directory: str

class BaseTask(BaseModel):
    auth: Auth = None
    builder: str = None
    cache: bool = None
    context: Context = None
    code: str = None
    command: str = None
    data: dict = None
    description: str = None
    destination: Union[
        RegistryDestination,
        LocalDestination
    ] = None
    execution_profile: TaskExecutionProfile = TaskExecutionProfile()
    git_repositories: List[GitRepository] = None
    headers: dict = None
    http_method: str = None
    image: str = None
    installer: EnumInstaller = None
    input: Input = {}
    id: ID
    _if: str = None
    output: Output = {}
    packages: List[str] = None
    poll: bool = None
    query_params: str = None
    type: str
    depends_on: List[TaskDependency] = []
    retries: int = 0
    runtime: EnumRuntimeEnvironment = None
    tapis_actor_id: str = None
    tapis_actor_message: Union[str, dict] = None
    tapis_job_def: dict = None
    url: str = None

    # Validators
    # _validate_id = validator("id", allow_reuse=True)(validate_id)

    class Config:
        arbitrary_types_allowed = True

class ContainerRunTask(BaseTask):
    type: Literal["container_run"]
    image: str

class ImageBuildTask(BaseTask):
    type: Literal["image_build"]
    builder: str
    cache: bool = False
    context: Context
    destination: Union[
        RegistryDestination,
        LocalDestination
    ]

    @root_validator
    def validate_image_build(cls, values):
        builder = values.get("builder")
        context = values.get("context")
        destination = values.get("destination")
        # Only allow context type of dockerhub when singularity is chosen
        # as a the image builder
        if (
            context.type == EnumContextType.Dockerhub
            and builder != EnumImageBuilder.Singularity
        ):
            raise ValueError("Context type 'dockerhub' can only be used in conjunction with a builder of type 'singularity'")
        
        if (
            context.type == EnumContextType.Dockerhub
            and destination.type != EnumDestinationType.Local
        ):
            raise ValueError("Context type 'dockerhub' can only be used in conjunction with destination of type `local`")

        return values
    
    @root_validator
    def validate_ctx_authn(cls, values):
        # Requester must provide an identity or credential in order
        # to pull from a private repository
        context = values.get("context")
        if (
            context.visibility == EnumVisibility.Private
            and (context.identity_uuid == None and context.credentials == None)
        ):
            raise ValueError(f"Any Context of an image build task with visibilty `{EnumVisibility.Private}` must have an identity_uuid or credentials.")

        return values

class TapisActorTask(BaseTask):
    type: Literal["tapis_actor"]
    tapis_actor_id: str
    poll: bool = True
    tapis_actor_message: str = None

class TapisJobTask(BaseTask):
    type: Literal["tapis_job"]
    tapis_job_def: dict
    poll: bool = True

class RequestTask(BaseTask):
    type: Literal["request"]
    http_method: str
    url: str

class FunctionTask(BaseTask):
    type: Literal["function"]
    git_repositories: List[GitRepository] = []
    runtime: EnumRuntimeEnvironment
    packages: List[str] = []
    installer: EnumInstaller
    code: str
    command: str = None

# Pipelines

Task = Annotated[
    Union[
        ContainerRunTask,
        ImageBuildTask,
        FunctionTask,
        RequestTask,
        TapisActorTask,
        TapisJobTask,
    ],
    Field(discriminator="type")
]

class BasePipeline(BaseModel):
    id: ID
    type: EnumPipelineType = EnumPipelineType.Workflow
    tasks: List[Task] = []
    execution_profile: ExecutionProfile = ExecutionProfile(
        max_exec_time=DEFAULT_MAX_EXEC_TIME*3)
    cron: str = None
    archive_ids: List[str] = []
    env: KeyVal = {}
    params: Params = {}

    # Validators
    # _validate_id = validator("id", allow_reuse=True)(validate_id)

class WorkflowPipeline(BasePipeline):
    pass

class CIPipeline(BasePipeline):
    cache: bool = False
    builder: str
    context: Context
    destination: Union[
        RegistryDestination,
        LocalDestination
    ] = None
    auth: dict = None
    data: dict = None
    headers: dict = None
    http_method: str = None
    query_params: dict = None
    url: str = None

class TapisRemoteIOBox(BaseModel):
    system_id: str
    path: str

class ETLPipeline(BasePipeline):
    source: TapisRemoteIOBox
    destination: TapisRemoteIOBox
    jobs: List[object]

# Pipeline runs and task executions
class TaskExecution(BaseModel):
    task_id: str
    started_at: str = None
    last_modified: str = None
    uuid: str

class PipelineRun(BaseModel):
    last_modified: str = None
    status: str = None
    uuid: str

class WorkflowSubmissionRequestMeta(BaseModel):
    idempotency_key: Union[str, List[str]]
    origin: str

class Group(BaseModel):
    id: str

class WorkflowSubmissionRequest(BaseModel, extra=Extra.allow):
    env: KeyVal
    params: Params
    group: Group
    pipeline: BasePipeline
    pipeline_run: PipelineRun
    meta: WorkflowSubmissionRequestMeta


