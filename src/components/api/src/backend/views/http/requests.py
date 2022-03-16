from typing import AnyStr, List, Union, Dict
from pydantic import BaseModel, StrictStr


# Auth
class AuthRequest(BaseModel):
    username: str
    password: str

# Identities
class IdentityCreateRequest(BaseModel):
    type: str
    username: str
    value: str
    group_id: str

# Contexts
class ContextCredential(BaseModel):
    token: str
    username: str = None

class Context(BaseModel):
    credential: ContextCredential = None
    branch: str
    dockerfile_path: str = "Dockerfile"
    sub_path: str = None
    type: str
    url: str
    visibility: str

# Destination
class DestinationCredential(BaseModel):
    token: str
    username: str

class Destination(BaseModel):
    credential: DestinationCredential
    tag: str
    type: str
    url: str

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

# Groups
class GroupCreateRequest(BaseModel):
    id: str
    users: List[StrictStr] = []

class GroupPutPatchRequest(BaseModel):
    users: List[StrictStr] = []

# Actions
class ActionDependency(BaseModel):
    name: str
    can_fail: bool = False

IOValueType = Union[AnyStr, Dict, List, bool]

class Input(BaseModel):
    type: str
    mode: str
    value: IOValueType

InputType = Dict[str, Input]

class Output(BaseModel):
    type: str
    model: str
    value: IOValueType

OutputType = Dict[str, Output]

class BaseAction(BaseModel):
    auth: dict = None
    auto_build: bool = None
    builder: str = None
    cache: bool = None
    context: Context = None
    data: dict = None
    description: str = None
    destination: Destination = None
    headers: dict = None
    http_method: str = None
    image: str = None
    input: InputType = None
    name: str
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

class ContainerRunAction(BaseAction):
    image: str

class ImageBuildAction(BaseAction):
    auto_build: bool = False
    builder: str = "kaniko"
    cache: bool = False
    context: Context
    destination: Destination

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
    type: str
    group_id: str
    actions: List[
        Union[
            ContainerRunAction,
            ImageBuildAction,
            TapisActorAction,
            TapisJobAction,
            WebhookAction
        ]
    ] = []
    run_on_create: bool = False

class CIPipeline(BasePipeline):
    cache: bool = False
    builder: str = "kaniko"
    context: Context
    destination: Destination
    auth: dict = None
    data: dict = None
    headers: dict = None
    http_method: str = None
    query_params: dict = None
    url: str = None

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