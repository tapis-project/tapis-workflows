import re

from typing import AnyStr, List, Literal, Union, Dict, TypedDict
from pydantic import BaseModel, validator, root_validator

from backend.models import (
    IMAGE_BUILDER_SINGULARITY,
    CONTEXT_TYPE_DOCKERHUB,
    VISIBILITY_PRIVATE,
    DESTINATION_TYPE_LOCAL,
    ARCHIVE_TYPE_IRODS,
    ARCHIVE_TYPE_S3,
    ARCHIVE_TYPE_SYSTEM,
    DEFAULT_ARCHIVE_DIR,
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

##################

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
    recipe_file_path: str = None
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

class ActionDependency(BaseModel):
    id: str
    can_fail: bool = False

    # Validators
    # _validate_id = validator("id", allow_reuse=True)(validate_id)

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

class BaseAction(BaseModel):
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
    headers: dict = None
    http_method: str = None
    image: str = None
    input: InputType = None
    id: str
    output: OutputType = None
    poll: bool = None
    query_params: str = None
    type: str
    depends_on: List[ActionDependency] = []
    retries: int = 0
    tapis_actor_id: str = None
    tapis_job_def: dict = None
    ttl: int = -1
    url: str = None

    # Validators
    # _validate_id = validator("id", allow_reuse=True)(validate_id)

class ContainerRunAction(BaseAction):
    image: str

class ImageBuildAction(BaseAction):
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
            and destination != DESTINATION_TYPE_LOCAL
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
            raise ValueError(f"Any Context of an image build action with visibilty `{VISIBILITY_PRIVATE}` must have an identity_uuid or credentials.")

        return values

class TapisActorAction(BaseAction):
    tapis_actor_id: str

class TapisJobAction(BaseAction):
    tapis_job_def: dict
    poll: bool = True

class WebhookAction(BaseAction):
    http_method: str
    url: str

# Pipelines
class BasePipeline(BaseModel):
    id: str
    type: str = "workflow"
    actions: List[
        Union[
            ContainerRunAction,
            ImageBuildAction,
            TapisActorAction,
            TapisJobAction,
            WebhookAction
        ]
    ] = []
    archive_ids: List[str]

    # Validators
    # _validate_id = validator("id", allow_reuse=True)(validate_id)

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

# Pipeline runs and action executions
class ActionExecution(BaseModel):
    action_id: str
    ended_at: str = None
    pipeline_run_id: str
    status: str

class PipelineRun(BaseModel):
    ended_at: str = None
    pipeline_id: str
    status: str
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


