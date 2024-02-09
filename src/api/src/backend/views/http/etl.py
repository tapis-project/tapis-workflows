from enum import Enum
from typing import List, Dict, Union, Literal, Annotated

from pydantic import BaseModel, validator, root_validator, Field

from .requests import _EnumMeta, Pipeline


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

class LocalIOBox(BaseModel):
    system_id: str
    data_path: str
    data_integrity_profile: DataIntegrityProfile = None
    manifests_path: str = None
    manifest_generation_policy: EnumManifestGenerationPolicy
    manifest_priority: EnumManifestPriority = EnumManifestPriority.Oldest
    exclude_pattern: str = None
    include_pattern: str = None

class LocalInbox(LocalIOBox):
    manifest_generation_policy: EnumManifestGenerationPolicy = EnumManifestGenerationPolicy.AutoOnePerFile

class LocalOutbox(LocalIOBox):
    manifest_generation_policy: EnumManifestGenerationPolicy = EnumManifestGenerationPolicy.AutoOneForAll

class GlobusLocalOutbox(LocalOutbox):
    globus_endpoint_id: str

class GlobusAuth(BaseModel):
    access_token: str = None
    refresh_token: str = None

class GlobusRemoteInbox(BaseModel):
    globus_auth: GlobusAuth
    globus_endpoint_id: str
    globus_client_id: str
    globus_destination_path: str

class TapisSystemRemoteInbox(BaseModel):
    system_id: str
    path: str

class S3Auth(BaseModel):
    access_key: str
    access_secret: str

class S3RemoteInbox(BaseModel):
    s3_auth: S3Auth
    url: str
    bucket: str

class TapisJobDef(BaseModel):
    pass

class TapisJobWorkflowsETL(BaseModel):
    input: str
    output: str

class TapisJobWorkflowsExtension(BaseModel):
    etl: TapisJobWorkflowsETL

class ExetendedTapisJob(TapisJobDef):
    workflows: TapisJobWorkflowsExtension = None

class TapisETLPipeline(Pipeline):
    remote_outbox: Dict = None
    local_inbox: LocalInbox
    jobs: List[ExetendedTapisJob]
    local_outbox: GlobusLocalOutbox
    remote_inbox: Union[
        TapisSystemRemoteInbox,
        GlobusRemoteInbox,
        S3RemoteInbox
    ]

    @validator("jobs")
    def one_or_more_jobs(cls, value):
        # Check that the pipeline contains at least 1 tapis job definition
        if len(value) < 1:
            raise ValueError("An ETL pipeline must contain at least 1 Tapis Job definition")
        
        return value