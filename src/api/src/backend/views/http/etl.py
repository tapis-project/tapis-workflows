from enum import Enum
from typing import List, Dict, Union

from pydantic import BaseModel

from . import _EnumMeta


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
    exclude_pattern: str = None

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

class TapisETLPipeline(BaseModel):
    remote_outbox: Dict = None
    local_inbox: LocalInbox
    jobs: List[Dict]
    local_outbox: LocalOutbox
    remote_inbox: GlobusRemoteInbox