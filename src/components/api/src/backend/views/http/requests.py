from typing import List, Union

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
    dockerfile_path: str
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
class EventCreateRequest(BaseModel):
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

class BaseAction(BaseModel):
    description: str = None
    name: str
    pipeline_id: str
    stage: str
    type: str
    depends_on: List[ActionDependency] = []
    retries: int = 0
    ttl: int = -1

class ContainerRunAction(BaseAction):
    pass

class ImageBuildAction(BaseAction):
    builder: str = "kaniko"
    cache: bool = False
    context: Context
    description: str = None
    destination: Destination

class TapisActorAction(BaseAction):
    tapis_actor_id: str

class TapisJobAction(BaseAction):
    tapis_job_definition: dict

class WebhookAction(BaseAction):
    auth: dict = None
    data: dict = None
    headers: dict = None
    http_method: str
    params: dict = None
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

class CIPipeline(BasePipeline):
    auto_build: bool = False
    cache: bool = False
    builder: str = "kaniko"
    context: Context
    destination: Destination
    auth: dict = None
    data: dict = None
    headers: dict = None
    http_method: str = None
    params: dict = None
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