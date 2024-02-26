from enum import Enum
from typing import Union, Literal, Annotated

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

class IOSystemProfile(BaseModel):
    path: str
    include_pattern: str = None
    exclude_pattern: str = None

class DataProfile(IOSystemProfile):
    integrity_profile: DataIntegrityProfile = None

class ManifestsProfile(IOSystemProfile):
    generation_policy: EnumManifestGenerationPolicy = None
    priority: EnumManifestPriority = None

class IngressProfile(IOSystemProfile):
    pass

class IOSystem(BaseModel):
    ingress: IngressProfile = None
    data: DataProfile
    manifests: ManifestsProfile

