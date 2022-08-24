from enum import Enum

from pydantic import BaseModel


class ResourceType(str, Enum):
    job = "job"
    configmap = "configmap"

class Resource(BaseModel):
    type: ResourceType

class ConfigMapResource(Resource):
    type = ResourceType.configmap
    configmap: object

class JobResource(Resource):
    type = ResourceType.job
    job: object
