from enum import Enum
from pydantic import BaseModel
from typing import Literal, Union

from owe_python_sdk.schema import _EnumMeta


class EnumTapisTaskOutputType(str, Enum, metaclass=_EnumMeta):
    TapisJob = "tapis_job"

class BaseTapisTaskOutput(BaseModel):
    type: EnumTapisTaskOutputType

class TapisSystemFileListItem:
    mimeType: str = None
    type: Literal["file", "dir"]
    owner: Union[str, int]
    group: Union[str, int]
    nativePermissions: str
    url: str
    lastModified: str
    name: str
    path: str
    size: int

class TapisJobTaskOutput(BaseTapisTaskOutput):
    type: EnumTapisTaskOutputType.TapisJob
    file: TapisSystemFileListItem