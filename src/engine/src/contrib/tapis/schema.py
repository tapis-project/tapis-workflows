from enum import Enum
from pydantic import BaseModel
from typing import Literal, Union

from owe_python_sdk.schema import _EnumMeta


class EnumTapisTaskOutputType(str, Enum, metaclass=_EnumMeta):
    TapisJob = "tapis_job"

class BaseTapisTaskOutput(BaseModel):
    type: EnumTapisTaskOutputType

class TapisSystemFile(BaseModel):
    mimeType: str = None
    type: Literal["file", "dir"]
    owner: Union[str, int] = None
    group: Union[str, int] = None
    nativePermissions: str = None
    url: str
    lastModified: str = None
    name: str
    path: str
    size: int = None

class TapisJobTaskOutput(BaseTapisTaskOutput):
    type: EnumTapisTaskOutputType.TapisJob
    system_id: str
    file: TapisSystemFile