from typing import  List

from pydantic import BaseModel, StrictStr


# Auth
class AuthRequest(BaseModel):
    username: str
    password: str

# Contexts
class ContextCredential(BaseModel):
    token: str
    username: str = None

class Context(BaseModel):
    credential: ContextCredential = None
    branch: str
    dockerfile_path: str
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
    context: str
    username: str

# Groups
class GroupCreateRequest(BaseModel):
    id: str
    users: List[StrictStr] = []

class GroupPutPatchRequest(BaseModel):
    users: List[StrictStr] = []

class PipelineCreateRequest(BaseModel):
    id: str
    auto_build: bool = False
    cache: bool = False
    builder: str = "kaniko"
    group_id: str
    context: Context
    destination: Destination

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