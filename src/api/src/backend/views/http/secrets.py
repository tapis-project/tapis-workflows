from typing import Any, Dict

from pydantic import BaseModel


class ReqCreateSecret(BaseModel):
    id: str
    description: str = None
    data: Dict[str, Any]