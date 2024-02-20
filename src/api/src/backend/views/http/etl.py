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

class IOBox(BaseModel):
    data_path: str
    data_integrity_profile: DataIntegrityProfile = None
    manifests_path: str = None
    exclude_pattern: str = None
    include_pattern: str = None

class DataEgress(IOBox):
    manifest_generation_policy: EnumManifestGenerationPolicy = EnumManifestGenerationPolicy.AutoOnePerFile
    manifest_priority: EnumManifestPriority = EnumManifestPriority.Oldest

class DataIngress(IOBox):
    pass

class RemoteOutbox(DataEgress):
    manifest_generation_policy: EnumManifestGenerationPolicy = EnumManifestGenerationPolicy.AutoOnePerFile
    manifest_priority: EnumManifestPriority = EnumManifestPriority.Oldest

class LocalInbox(DataIngress):
    pass

class LocalOutbox(DataEgress):
    manifest_generation_policy: EnumManifestGenerationPolicy = EnumManifestGenerationPolicy.AutoOneForAll
    manifest_priority: EnumManifestPriority = None

class RemoteInbox(DataIngress):
    pass

