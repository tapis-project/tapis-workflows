from enum import Enum

from pydantic import BaseModel


class ResourceType(str, Enum):
    job = "job"
    config_map = "config_map"
    file = "file"

class Resource(BaseModel):
    type: ResourceType

class FileResource(Resource):
    type = ResourceType.file
    path: str

class ConfigMapResource(Resource):
    type = ResourceType.config_map
    name: str

class JobResource(Resource):
    type = ResourceType.job
    name: str
