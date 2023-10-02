import re

from enum import Enum, EnumMeta
from typing import List, Literal, Union, Dict, TypedDict, get_args
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

LiteralArchiveTypes = Literal["irods", "s3", "system"]
ArchiveTypes = list(get_args(LiteralArchiveTypes))
class EnumArchiveType(str, Enum, metaclass=_EnumMeta):
    Irods = "irods"
    S3 = "s3"
    System = "system"

LiteralContextTypes = Literal["github", "dockerhub", "gitlab"]
ContextTypes = list(get_args(LiteralContextTypes))
class EnumContextType(str, Enum, metaclass=_EnumMeta):
    Github = "github"
    Gitlab = "gitlab"
    Dockerhub = "dockerhub"

LiteralDestinationTypes = Literal["dockerhub", "local", "s3"]
DestinationTypes = list(get_args(LiteralDestinationTypes))
class EnumDestinationType(str, Enum, metaclass=_EnumMeta):
    Dockerhub = "dockerhub"
    DockerhubLocal = "dockerhub_local"
    Local = "local"
    S3 = "s3"

LiteralDuplicateSubmissionPolicies = Literal["allow", "deny", "terminate", "defer"]
DuplicateSubmissionPolicies = list(get_args(LiteralDuplicateSubmissionPolicies))
class EnumDuplicateSubmissionPolicy(str, Enum, metaclass=_EnumMeta):
    Allow = "allow",
    Deny = "deny"
    Terminate = "terminate"
    Defer = "defer"

LiteralImageBuilders = Literal["kaniko", "singularity"]
ImageBuilders = list(get_args(LiteralImageBuilders))
class EnumImageBuilder(str, Enum, metaclass=_EnumMeta):
    Kaniko = "kaniko"
    Singularity = "singularity"

LiteralRuntimeEnvironments = Literal["python:3.9"]
RuntimeEnvironments = list(get_args(LiteralRuntimeEnvironments))
class EnumRuntimeEnvironment(str, Enum, metaclass=_EnumMeta):
    Python39 = "python:3.9"
    PythonSingularity = "tapis/workflows-python-singularity:0.1.0"

LiteralInstallers = Literal["pip", "apt_get"]
Installers = list(get_args(LiteralInstallers))
class EnumInstaller(str, Enum, metaclass=_EnumMeta):
    Pip = "pip"
    AptGet = "apt_get"

LiteralPipelineTypes = Literal["workflow", "ci"]
PipelineTypes = list(get_args(LiteralPipelineTypes))
class EnumPipelineType(str, Enum, metaclass=_EnumMeta):
    Workflow = "workflow"
    CI = "ci"

LiteralRetryPolicies = Literal["exponential_backoff"]
RetryPolicies = list(get_args(LiteralRetryPolicies))
class EnumRetryPolicy(str, Enum, metaclass=_EnumMeta):
    ExponentialBackoff = "exponential_backoff"

LiteralInvocationModes = Literal["async", "sync"]
InvocationModes = list(get_args(LiteralInvocationModes))
class EnumInvocationMode(str, Enum, metaclass=_EnumMeta):
    Async = "async"
    Sync = "sync"

LiteralTaskIOTypes = Literal["string", "number", "boolean", "string_array", "number_array", "boolean_array", "mixed_arrray", "tapis_file_input", "tapis_file_input_array"]
TaskIOTypes = list(get_args(LiteralTaskIOTypes))
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

LiteralTaskInputValueFromKeys = Literal["env", "params", "task_output"]
TaskInputValueFromKeys = list(get_args(LiteralTaskInputValueFromKeys))
class EnumTaskInputValueFromKey(str, Enum, metaclass=_EnumMeta):
    Env = "env"
    Params = "params"
    TaskOutput = "task_output"

LiteralTaskFlavors = Literal["c1tiny", "c1xxsml", "c1xsml", "c1sml", "c1med", "c1lrg", "c1xlrg", "c1xxlrg", "g1nvdsml", "g1nvdmed", "g1nvdlrg"]
TaskFlavors = list(get_args(LiteralTaskFlavors))
class EnumTaskFlavor(str, Enum, metaclass=_EnumMeta):
    C1_TINY = "c1tiny"
    C1_XXSML = "c1xxsml"
    C1_XSML = "c1xsml"
    C1_SML = "c1sml"
    C1_MED = "c1med"
    C1_LRG = "c1lrg"
    C1_XLRG = "c1xlrg"
    C1_XXLRG = "c1xxlrg"
    G1_NVD_SML = "g1nvdsml"
    G1_NVD_MED = "g1nvdmed"
    G1_NVD_LRG = "g1nvdlrg"

LiteralTaskTypes = Literal["function", "application", "request", "image_build", "tapis_job", "tapis_actor"]
TaskTypes = list(get_args(LiteralTaskTypes))
class EnumTaskType(str, Enum, metaclass=_EnumMeta):
    ImageBuild = "image_build"
    Request = "request"
    Function = "function"
    ContainerRun = "container_run"
    Application = "application"
    TapisActor = "tapis_actor"
    TapisJob = "tapis_job"

LiteralVisibilties = Literal["private", "public"]
Visibilities = list(get_args(LiteralVisibilties))
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

class BaseValue(BaseModel):
    type: EnumTaskIOTypes = EnumTaskIOTypes.String
    value: Union[str, int, float, bool, bytes] = None
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
        # Nothing to validate if there is not value_from property
        if value == None: return value
        if type(value) not in [str, bool, int, float, bytes]:
            raise TypeError("Variable values must be a string, number, bytes, or boolean'")

        return value

    @validator("value_from", pre=True)
    def value_from_type_validation(cls, value):
        # Nothing to validate if there is not value_from property
        if value == None: return value
        is_dict = type(value) == dict
        is_valid = len([
            k for k in value if (
            (
                type(k) == str 
                and (
                    (k in ["env", "params"] and type(value[k]) == str)
                    or (k in ["task_output", "secret", "host"] and type(value[k]) == dict)
                )
            )
        )]) < 1
        if (not is_dict or (is_dict and is_valid)):
            raise TypeError(
                "Task Input Value Error: 'value_from' property must be a single key-value pair where the key is oneOf ['env', 'params', 'task_input', 'host', 'secret'] and the value is a non-empty string if key is oneOf ['env', 'params'] or an object if key is oneOf ['task_input', 'host', 'secret']"
            )
        return value
    

class TaskOutputRef(BaseModel):
    task_id: str
    output_id: str

LiteralHostRefTypes = Literal["kubernetes_secret", "kubernetes_config_map"]
class ValueFromHostRef(BaseModel):
    type: LiteralHostRefTypes
    name: str
    field_selector: str = None

class ValueFromSecretRef(BaseModel):
    engine: str
    pk: str
    field_selector: str = None

ValueFromEnv = Dict[Literal["env"], str]
ValueFromParams = Dict[Literal["params"], str]
ValueFromTaskOutput = Dict[Literal["task_output"], TaskOutputRef]
ValueFromHost = Dict[Literal["host"], ValueFromHostRef]
ValueFromSecret = Dict[Literal["secret"], ValueFromSecretRef]

class TaskInputValue(BaseValue):
    type: EnumTaskIOTypes
    value: Union[str, int, float, bool, bytes] = None
    value_from: Union[
        ValueFromEnv,
        ValueFromParams,
        ValueFromTaskOutput,
        ValueFromHost,
        ValueFromSecret
    ] = None

class ValueWithRequirements(BaseValue):
    required: bool = False

KeyVal = Dict[str, BaseValue]
################## /Common ###################

class S3Auth(BaseModel):
    access_key: str
    access_secret: str

class IRODSAuth(BaseModel):
    user: str
    password: str

# Archive
class BaseArchive(BaseModel):
    id: ID
    type: LiteralArchiveTypes
    credentials: Union[
        S3Auth,
        IRODSAuth
    ] = None
    identity_uuid: str = None

    class Config:
        extra = Extra.allow

class TapisSystemArchive(BaseArchive):
    type: Literal["system"]
    system_id: str
    archive_dir: str = DEFAULT_ARCHIVE_DIR # Relative to the system's RootDir

class S3Archive(BaseArchive):
    type: Literal["s3"]
    credentials: S3Auth = None
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


class IRODSArchive(BaseArchive):
    type: Literal["irods"]
    credentials: IRODSAuth = None
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

Archive = Annotated[
    Union[
        TapisSystemArchive,
        IRODSArchive,
        S3Archive
    ],
    Field(discriminator="type")
]

class AddRemoveArchive(BaseModel):
    archive_id: str

# Auth
class AuthRequest(BaseModel):
    username: str
    password: str

class GithubAuth(BaseModel):
    username: str
    personal_access_token: str

class DockerhubAuth(BaseModel):
    username: str
    token: str

class IdentityCreateRequest(BaseModel):
    type: str
    name: str
    description: str = None
    credentials: Union[
        GithubAuth,
        DockerhubAuth
    ]

class BaseContext(BaseModel):
    type: LiteralContextTypes
    branch: str = None
    build_file_path: str = None
    credentials: Union[
        GithubAuth,
        DockerhubAuth
    ] = None
    identity_uuid: str = None
    sub_path: str = None
    tag: str = None
    url: str
    visibility: str

    class Config:
        extra: Extra.allow

class GithubContext(BaseContext):
    type: Literal["github"]
    credentials: GithubAuth = None
    branch: str
    build_file_path: str = None
    sub_path: str = None

class DockerhubContext(BaseContext):
    type: Literal["dockerhub"]
    credentials: DockerhubAuth = None

# TODO add more types to the destination credential types as they become supported
DestinationCredentialTypes = DockerhubAuth

class BaseDestination(BaseModel):
    type: LiteralDestinationTypes

class DockerhubDestination(BaseDestination):
    type: Literal["dockerhub"]
    tag: str = None
    credentials: DockerhubAuth = None
    identity_uuid: str = None
    url: str

    @root_validator(skip_on_failure=True)
    def creds_or_identity(csl, values):
        creds, identity = values.get("credentials"), values.get("identity_uuid")
        if creds == None and identity == None:
            raise ValueError("Missing credentials and identity_uuid. Must provide at lease one.")

        return values

class LocalDestination(BaseDestination):
    type: Literal["local"]
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

# Output -----------------------------------------------------------------

class BaseOutputValue(BaseModel):
    type: EnumTaskIOTypes
    value: Union[str, int, float, bool, bytes]

# ------------------------------------------------------------------------

class HTTPBasicAuthCreds(BaseModel):
    username: str = None
    password: str = None

class Auth(BaseModel):
    type: str = "http_basic_auth"
    creds: HTTPBasicAuthCreds

class BaseExecutionProfile(BaseModel):
    max_exec_time: int = DEFAULT_MAX_EXEC_TIME
    invocation_mode: str = EnumInvocationMode.Async
    retry_policy: str = EnumRetryPolicy.ExponentialBackoff
    max_retries: int = DEFAULT_MAX_RETRIES

class PipelineExecutionProfile(BaseExecutionProfile):
    duplicate_submission_policy: str = EnumDuplicateSubmissionPolicy.Terminate

class TaskExecutionProfile(BaseExecutionProfile):
    flavor: EnumTaskFlavor = EnumTaskFlavor.C1_MED

class GitRepository(BaseModel):
    url: str
    branch: str = None
    auth: GithubAuth = None

class ClonedGitRepository(GitRepository):
    directory: str

class Uses(BaseModel):
    repository: GitRepository

class BaseTask(BaseModel):
    id: ID
    type: LiteralTaskTypes
    uses: Uses = None
    depends_on: List[TaskDependency] = []
    description: str = None
    execution_profile: TaskExecutionProfile = TaskExecutionProfile()
    input: Dict[str, TaskInputValue] = {}
    conditional: str = None
    output: Dict[str, BaseOutputValue] = {}

    class Config:
        arbitrary_types_allowed = True
        extra = Extra.allow

    @root_validator(pre=True)
    def backwards_compatibility_transforms(cls, values):
        # Transform None for inputs and outputs to empty dict
        props_to_transfom = ["input", "output"]
        for prop in props_to_transfom:
            if values.get(prop, None) == None:
                values[prop] = {}

        # Where git_repositories on tasks == None, set to empty array
        if values.get("git_repositories", None) == None:
            values["git_repositories"] = []

        # Where values set directly on input, convert to use dict with "value" prop
        for key, value in values.get("input").items():
            if type(value) != dict:
                values["input"][key] = {
                    "value": value
                }

        return values

class ApplicationTask(BaseTask):
    type: Literal["application", "container_run"]
    image: str

class ImageBuildTask(BaseTask):
    type: Literal["image_build"]
    builder: str
    cache: bool = False
    context: Annotated[
        Union[
            DockerhubContext,
            GithubContext
        ],
        Field(discriminator="type")
    ]
    destination: Annotated[
        Union[
            DockerhubDestination,
            LocalDestination
        ],
        Field(discriminator="type")
    ] = None

    @root_validator(skip_on_failure=True)
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
    
    @root_validator(skip_on_failure=True)
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
    git_repositories: List[ClonedGitRepository] = []
    runtime: EnumRuntimeEnvironment
    packages: List[str] = []
    installer: EnumInstaller
    code: str
    command: str = None

# Pipelines

Task = Annotated[
    Union[
        ApplicationTask,
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
    tasks: List[
        Annotated[
            Union[
                ApplicationTask,
                ImageBuildTask,
                FunctionTask,
                RequestTask,
                TapisActorTask,
                TapisJobTask,
            ],
            Field(discriminator="type")
        ]
    ] = []
    execution_profile: PipelineExecutionProfile = PipelineExecutionProfile(
        max_exec_time=DEFAULT_MAX_EXEC_TIME*3)
    cron: str = None
    archive_ids: List[str] = []
    env: KeyVal = {}
    params: Dict[str, ValueWithRequirements] = {}

    # NOTE This pre validation transformer is for backwards-compatibility
    # Previous pipelines did not have environments or parmas
    @root_validator(pre=True)
    def backwards_compatibility_transforms(cls, values):
        props_to_transfom = ["env", "params"]
        for prop in props_to_transfom:
            if values.get(prop, None) == None:
                values[prop] = {}

        # Where values set directly on env, convert to use dict with "value" prop
        for key, value in values.get("env").items():
            if type(value) != dict:
                values["env"][key] = {
                    "value": value
                }
        
        return values
    class Config:
        extra = Extra.allow

class WorkflowPipeline(BasePipeline):
    pass

class CIPipeline(BasePipeline):
    cache: bool = False
    builder: str
    context: Annotated[
        Union[
            DockerhubContext,
            GithubContext
        ],
        Field(discriminator="type")
    ]
    destination: Annotated[
        Union[
            DockerhubDestination,
            LocalDestination
        ],
        Field(discriminator="type")
    ] = None
    auth: dict = None
    data: dict = None
    headers: dict = None
    http_method: str = None
    query_params: dict = None
    url: str = None

# Pipeline runs and task executions
# TODO rename ReqCreateTaskExecution
class TaskExecution(BaseModel):
    task_id: str
    started_at: str = None
    last_modified: str = None
    uuid: str
    last_message: str = None
    stdout: str = None
    stderr: str = None

class ReqPatchTaskExecution(BaseModel):
    uuid: str
    last_message: str = None
    stdout: str = None
    stderr: str = None

class PipelineRun(BaseModel):
    last_modified: str = None
    status: str = None
    uuid: str
    logs: str = None

class ReqPatchPipelineRun(BaseModel):
    status: str = None
    uuid: str
    logs: str = None

class WorkflowSubmissionRequestMeta(BaseModel):
    idempotency_key: Union[str, List[str]]
    origin: str

    class Config:
        extra = Extra.allow

class Group(BaseModel):
    id: str

class WorkflowSubmissionRequest(BaseModel):
    archives: List[Archive] = []
    env: KeyVal = {}
    params: KeyVal = {}
    group: Group
    pipeline: BasePipeline
    pipeline_run: PipelineRun
    meta: WorkflowSubmissionRequestMeta

    class Config:
        extra = Extra.allow

    # NOTE This pre validation transformer is for backwards-compatibility
    # Previous workflow submissions did not have environments or parmas
    @root_validator(pre=True)
    def backwards_compatibility_transforms(cls, values):
        props_to_transfom = ["env", "params"]
        for prop in props_to_transfom:
            if values.get(prop, None) == None:
                values[prop] = {}

        # Where values set directly on env, convert to use dict with "value" prop
        for key, value in values.get("env").items():
            if type(value) != dict:
                values["env"][key] = {
                    "value": value
                }

        return values

# Generic object. NOTE Only used in idempotency key resolution
class EmptyObject(BaseModel):
    pass

class PreparedRequest:
    def __init__(
        self,
        is_valid=True,
        body=None,
        message=None,
        failure_view=None
    ):
        self.is_valid = is_valid
        self.body = body
        self.message = message
        self.failure_view = failure_view


