from typing import Optional, List

from pydantic import BaseModel, StrictStr

# Auth
class AuthRequest(BaseModel):
    username: str
    password: str

# Groups
class CreateGroupRequest(BaseModel):
    id: str
    users: List[StrictStr] = []

class PutPatchGroupRequest(BaseModel):
    users: List[StrictStr] = []

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