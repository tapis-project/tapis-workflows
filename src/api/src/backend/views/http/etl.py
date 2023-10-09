from enum import Enum
from typing import List, Dict, Union

from pydantic import BaseModel

from .requests import _EnumMeta, Pipeline


class EnumManifestGenerationPolicy(str, Enum, metaclass=_EnumMeta):
    OnePerFile = "one_per_file"
    OneForAll = "one_for_all"

class EnumManifestPriority(str, Enum, metaclass=_EnumMeta):
    Oldest = "oldest"
    Newest = "newest"
    Any = "any"

class LocalIOBox(BaseModel):
    system_id: str
    data_path: str
    manifest_generation_policy: EnumManifestGenerationPolicy
    manifest_priority: EnumManifestPriority = EnumManifestPriority.Oldest
    manifests_path: str = None
    exclude_pattern: List[str] = []

class LocalInbox(LocalIOBox):
    manifest_generation_policy: EnumManifestGenerationPolicy = EnumManifestGenerationPolicy.OnePerFile

class LocalOutbox(LocalIOBox):
    manifest_generation_policy: EnumManifestGenerationPolicy = EnumManifestGenerationPolicy.OneForAll
    zip: bool = False

class GlobusLocalOutbox(LocalOutbox):
    globus_endpoint_id: str

class GlobusAuth(BaseModel):
    access_token: str = None
    refresh_token: str = None

class GlobusRemoteInbox(BaseModel):
    globus_auth: GlobusAuth
    globus_endpoint_id: str
    globus_client_id: str

class S3Auth(BaseModel):
    access_key: str
    access_secret: str

class S3RemoteInbox(BaseModel):
    s3_auth: S3Auth
    url: str
    bucket: str

class TapisETLPipeline(Pipeline):
    remote_outbox: Dict = None
    local_inbox: LocalInbox
    jobs: List[Dict]
    local_outbox: LocalOutbox
    remote_inbox: Union[
        GlobusRemoteInbox,
        S3RemoteInbox
    ]
    followup_tasks: List[Dict] = []