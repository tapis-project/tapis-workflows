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
    configmap: object

class JobResource(Resource):
    type = ResourceType.job
    job: object
