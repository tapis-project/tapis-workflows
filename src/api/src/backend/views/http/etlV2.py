from enum import Enum
from typing import Union, Literal, Annotated, List

from pydantic import BaseModel, Field

from .requests import _EnumMeta


class EnumManifestGenerationPolicy(str, Enum, metaclass=_EnumMeta):
    Manual = "manual"
    AutoOnePerFile = "auto_one_per_file"
    AutoOneForAll = "auto_one_for_all"

class EnumManifestPriority(str, Enum, metaclass=_EnumMeta):
    Oldest = "oldest"
    Newest = "newest"
    Any = "any"

class BaseDataIntegrityProfile(BaseModel):
    type: Literal["checksum", "byte_check", "done_file"]

class ChecksumDataIntegrityProfile(BaseDataIntegrityProfile):
    type: Literal["checksum"]

class ByteCheckDataIntegrityProfile(BaseDataIntegrityProfile):
    type: Literal["byte_check"]

class DoneFileDataIntegrityProfile(BaseDataIntegrityProfile):
    type: Literal["done_file"]
    done_files_path: str
    include_pattern: str = None
    exclude_pattern: str = None

DataIntegrityProfile = Annotated[
    Union[
        ChecksumDataIntegrityProfile,
        ByteCheckDataIntegrityProfile,
        DoneFileDataIntegrityProfile
    ],
    Field(discriminator="type")
]

class IOProfile(BaseModel):
    data_path: str
    data_integrity_profile: DataIntegrityProfile = None
    manifests_path: str = None
    exclude_pattern: str = None
    include_pattern: str = None

class ETLSystem(BaseModel):
    writable: bool = True
    ingress_profile: IOProfile
    egress_profile: IOProfile

class EnumXferAction(str, Enum, metaclass=_EnumMeta):
    PUSH = "push"
    PULL = "pull"
    NOOP = "noop"
    
class ETLCycle(BaseModel):
    ingress: ETLSystem
    egress: ETLSystem
    xfer_action: EnumXferAction
    transforms: List[object]
    
    