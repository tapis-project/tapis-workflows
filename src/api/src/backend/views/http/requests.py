import re

from enum import Enum
from typing import AnyStr, List, Union, Dict, TypedDict, Literal, Optional
from typing_extensions import Annotated
from pydantic import BaseModel, validator, root_validator, Field

from backend.models import (
    IMAGE_BUILDER_SINGULARITY,
    CONTEXT_TYPE_DOCKERHUB,
    VISIBILITY_PRIVATE,
    DESTINATION_TYPE_LOCAL,
    ARCHIVE_TYPE_IRODS,
    ARCHIVE_TYPE_S3,
    ARCHIVE_TYPE_SYSTEM,
    DEFAULT_ARCHIVE_DIR,
    DEFAULT_TASK_INVOCATION_MODE,
    DEFAULT_MAX_EXEC_TIME,
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_POLICY,
    DEFAULT_DUPLICATE_SUBMISSION_POLICY
)

ARCHIVE_TYPES = [ARCHIVE_TYPE_IRODS, ARCHIVE_TYPE_S3, ARCHIVE_TYPE_SYSTEM]

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
class EnumValueType(str, Enum):
    String = "string"
    Number = "number"
    Boolean = "boolean"

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
                "The value of an Variable's 'value_from' property must be a single key-value pair where both the key and the value are non-empty strings")
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
    id: str
    credentials: Union[
        S3Credentials,
        IRODSCredentials
    ] = None
    identity_uuid: str = None
    type: str

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
    type: str
    url: str
    visibility: str

    # Validators
    # _validate_url = validator("url", allow_reuse=True)(validate_ctx_dest_url)

# TODO add more types to the destination credential types as they become supported
DestinationCredentialTypes = DockerhubCredentials

class Destination(BaseModel):
    type: str
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
    id: str
    users: List[GroupUserReq] = []

    # Validators
    # _validate_id = validator("id", allow_reuse=True)(validate_id) 

class TaskDependency(BaseModel):
    id: str
    can_fail: bool = False

    # Validators
    # _validate_id = validator("id", allow_reuse=True)(validate_id)

# Task I/O Types ---------------------------------------------------------

TaskIOTypes = Union[
    Literal["string"],
    Literal["number"],
    Literal["boolean"],
    Literal["string_array"],
    Literal["number_array"],
    Literal["boolean_array"],
    Literal["mixed_array"],
    Literal["tapis_file_input"],
    Literal["tapis_file_input_array"]
]

task_input_value_types = [
    "string",
    "number",
    "boolean",
    "string_array",
    "number_array",
    "boolean_array",
    "mixed_array",
    "tapis_file_input",
    "tapis_file_input_array"
]
task_input_value_from_keys = ["env", "params", "task_output"]

class TaskOutputRef(BaseModel):
    task_id: str
    output_id: str

# Input -----------------------------------------------------------------

TaskInputValueFromKey = Union[
    Literal["env"],
    Literal["params"],
]

class BaseInputValue(BaseModel):
    type: TaskIOTypes
    value: Union[str, int, float, bytes] = None
    value_from: Union[
        Dict[TaskInputValueFromKey, str],
        Dict[Literal["task_output"], TaskOutputRef]
    ] = None

Input = Dict # TODO move validation logic to pydantic model

# Output -----------------------------------------------------------------

class BaseOutputValue(BaseModel):
    type: TaskIOTypes
    value: Union[str, int, float, bytes]

Output = Dict[str, BaseOutputValue]

# ------------------------------------------------------------------------

class HTTPBasicAuthCreds(BaseModel):
    username: str = None
    password: str = None

class Auth(BaseModel):
    type: str = "http_basic_auth"
    creds: HTTPBasicAuthCreds

class EnumTaskFlavor(str, Enum):
    C1_SML = "c1sml"
    C1_MED = "c1med"
    C1_LRG = "c1lrg"
    C1_XLRG = "c1xlrg"
    C1_XXLRG = "c1xxlrg"
    G1_NVD_SML = "g1nvdsml"
    G1_NVD_MED = "g1nvdmed"
    G1_NVD_LRG = "g1nvdlrg"

class ExecutionProfile(BaseModel):
    flavor: EnumTaskFlavor = None
    max_exec_time: int = DEFAULT_MAX_EXEC_TIME
    invocation_mode: str = DEFAULT_TASK_INVOCATION_MODE
    retry_policy: str = DEFAULT_RETRY_POLICY
    max_retries: int = DEFAULT_MAX_RETRIES
    duplicate_submission_policy: str = DEFAULT_DUPLICATE_SUBMISSION_POLICY

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
    execution_profile: ExecutionProfile = ExecutionProfile()
    headers: dict = None
    http_method: str = None
    image: str = None
    installer: str = None
    input: Input = {}
    id: str
    _if: str = None
    output: Output = {}
    packages: List[str] = None
    poll: bool = None
    query_params: str = None
    type: str
    depends_on: List[TaskDependency] = []
    retries: int = 0
    runtime: str = None
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
            context.type == CONTEXT_TYPE_DOCKERHUB
            and builder != IMAGE_BUILDER_SINGULARITY
        ):
            raise ValueError("Context type 'dockerhub' can only be used in conjunction with a builder of type 'singularity'")
        
        if (
            context.type == CONTEXT_TYPE_DOCKERHUB
            and destination.type != DESTINATION_TYPE_LOCAL
        ):
            raise ValueError("Context type 'dockerhub' can only be used in conjunction with destination of type `local`")

        return values
    
    @root_validator
    def validate_ctx_authn(cls, values):
        # Requester must provide an identity or credential in order
        # to pull from a private repository
        context = values.get("context")
        if (
            context.visibility == VISIBILITY_PRIVATE
            and (context.identity_uuid == None and context.credentials == None)
        ):
            raise ValueError(f"Any Context of an image build task with visibilty `{VISIBILITY_PRIVATE}` must have an identity_uuid or credentials.")

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
    runtime: str
    packages: List[str] = []
    installer: str
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
    id: str
    type: str = "workflow"
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
    pipeline_id: str
    status: str = None
    uuid: str

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


