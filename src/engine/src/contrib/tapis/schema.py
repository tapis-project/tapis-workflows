from uuid import uuid4

from typing import Literal, Union, List, Dict

from enum import Enum
from pydantic import BaseModel, Extra, root_validator, validator

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
    exec_system_output_dir: str
    file: TapisSystemFile

class ReqSubmitJob(BaseModel):
    name: str = None
    execSystemId: str = None
    fileInputs: List[Dict] = []
    fileInputArrays: List[Dict] = []
    execSystemInputDir: str
    appId: str
    appVersion: Union[str, int, float]

    class Config:
        extra = Extra.allow

    @root_validator(pre=True)
    def create_name(cls, values):
        if values.get("name", None) == None:
            values["name"] = "owe-" + str(uuid4())

        return values

    @validator("appVersion")
    def coerce_app_version(cls, value):
        if type(value) != str:
            value = str(value)

        return value
