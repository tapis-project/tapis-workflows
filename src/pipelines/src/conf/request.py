from typing import List, Dict, Annotated, Union, TypedDict, AnyStr, Literal
from pydantic import BaseModel, root_validator, Field

from conf.constants import (
    DEFAULT_MAX_EXEC_TIME,
    DEFAULT_INVOCATION_MODE,
    DEFAULT_RETRY_POLICY,
    DEFAULT_MAX_RETRIES,
    DEFAULT_DUPLICATE_SUBMISSION_POLICY
)

class Archivers(Dict):
    pass

class Backends(Dict):
    pass

class Meta(BaseModel):
    idempotency_key: List[str] = []

class Middleware(BaseModel):
    backends: Backends
    archivers: Archivers

class PipelineRun:
    uuid: str

# ___________________________________________
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
    archive_dir: str

class S3Archive(BaseArchive):
    credentials: S3Credentials
    endpoint: str
    bucket: str
    region: str

    @root_validator
    def validate_supported_types(cls, values):
        creds = values.get("credentials")

        if creds == None:
            raise ValueError("Archive of type `s3` must provide credentials")

        return values

class AddRemoveArchive(BaseModel):
    archive_id: str

class IRODSArchive(BaseArchive):
    credentials: S3Credentials = None
    host: str
    port: str

    @root_validator
    def validate_supported_types(cls, values):
        creds = values.get("credentials")

        if creds == None:
            raise ValueError("Archive of type `irods` must provide credentials")

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

class RegistryDestination(Destination):
    tag: str = None
    credentials: DestinationCredentialTypes = None
    url: str

class LocalDestination(Destination):
    filename: str = None

class TaskDependency(BaseModel):
    id: str
    can_fail: bool = False

IOValueType = Union[AnyStr, Dict, List, bool]

class Input(BaseModel):
    type: str
    value: IOValueType

InputType = Dict[str, Input]

class Output(BaseModel):
    type: str
    value: IOValueType

OutputType = Dict[str, Output]

class HTTPBasicAuthCreds(BaseModel):
    username: str = None
    password: str = None

class Auth(BaseModel):
    type: str = "http_basic_auth"
    creds: HTTPBasicAuthCreds

class ExecutionProfile(BaseModel):
    max_exec_time: int = DEFAULT_MAX_EXEC_TIME
    invocation_mode: str = DEFAULT_INVOCATION_MODE
    retry_policy: str = DEFAULT_RETRY_POLICY
    max_retries: int = DEFAULT_MAX_RETRIES
    duplicate_submission_policy: str = DEFAULT_DUPLICATE_SUBMISSION_POLICY

class BaseTask(BaseModel):
    auth: Auth = None
    builder: str = None
    cache: bool = None
    context: Context = None
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
    input: InputType = None
    id: str
    output: OutputType = None
    poll: bool = None
    query_params: str = None
    type: str
    depends_on: List[TaskDependency] = []
    retries: int = 0
    tapis_actor_id: str = None
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
            context.type == "dockerhub"
            and builder != "singularity"
        ):
            raise ValueError("Context type 'dockerhub' can only be used in conjunction with a builder of type 'singularity'")
        
        if (
            context.type == "dockerhub"
            and destination.type != "local"
        ):
            raise ValueError("Context type 'dockerhub' can only be used in conjunction with destination of type `local`")

        return values

class TapisActorTask(BaseTask):
    type: Literal["tapis_actor"]
    tapis_actor_id: str

class TapisJobTask(BaseTask):
    type: Literal["tapis_job"]
    tapis_job_def: dict
    poll: bool = True

class RequestTask(BaseTask):
    type: Literal["request"]
    http_method: str
    url: str

# Pipelines

Task = Annotated[
    Union[
        ContainerRunTask,
        ImageBuildTask,
        TapisActorTask,
        TapisJobTask,
        RequestTask
    ],
    Field(discriminator="type")
]

class BasePipeline(BaseModel):
    id: str
    type: str = "workflow"
    tasks: List[Task] = []
    execution_profile: ExecutionProfile = ExecutionProfile(
        max_exec_time=DEFAULT_MAX_EXEC_TIME)
    archive_ids: List[str] = []

    # Validators
    # _validate_id = validator("id", allow_reuse=True)(validate_id)
# ___________________________________________

class BaseRequest(BaseModel):
    pipeline: BasePipeline
    pipeline_run: PipelineRun
    middleware: Middleware
    meta: Meta = Meta()
