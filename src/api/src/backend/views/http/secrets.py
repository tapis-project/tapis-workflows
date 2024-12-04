from typing import Any, Dict, Union

from pydantic import BaseModel


class ReqCreateSecret(BaseModel):
    id: str
    description: str = None
    data: Union[
        Dict[str, Any],
        str,
        int,
        float,
        bool
    ]