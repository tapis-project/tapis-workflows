from typing import List, Dict, Literal

from pydantic import BaseModel, Extra, conlist

from .requests import Pipeline

from backend.views.http.etl import (
    EnumManifestGenerationPolicy,
    EnumManifestPriority,
    DataProfile,
    ManifestsProfile,
    IOSystem
)

class TapisIOSystemProfile(BaseModel):
    system_id: str

class RODataProfile(TapisIOSystemProfile, DataProfile):
    path: str = "/ETL/REMOTE-OUTBOX/DATA"

class ROManifestsProfile(TapisIOSystemProfile, ManifestsProfile):
    path: str = "/ETL/REMOTE-OUTBOX/MANIFESTS"
    generation_policy: EnumManifestGenerationPolicy = EnumManifestGenerationPolicy.AutoOnePerFile
    priority: EnumManifestPriority = EnumManifestPriority.Oldest
    
class RemoteOutbox(IOSystem):
    data: RODataProfile
    manifests: ROManifestsProfile

class LIDataProfile(TapisIOSystemProfile, DataProfile):
    path: str = "/ETL/LOCAL-INBOX/DATA"

class LIManifestsProfile(TapisIOSystemProfile, ManifestsProfile):
    path: str = "/ETL/LOCAL-INBOX/MANIFESTS"
    generation_policy: EnumManifestGenerationPolicy = None
    priority: EnumManifestPriority = EnumManifestPriority.Oldest

class LIControlProfile(TapisIOSystemProfile):
    path: str = "/ETL/LOCAL-INBOX/CONTROL"

class LocalInbox(IOSystem):
    data: LIDataProfile
    manifests: LIManifestsProfile
    control: LIControlProfile

class LODataProfile(TapisIOSystemProfile, DataProfile):
    path: str = "/ETL/LOCAL-OUTBOX/DATA"

class LOManifestsProfile(TapisIOSystemProfile, ManifestsProfile):
    path: str = "/ETL/LOCAL-OUTBOX/MANIFESTS"
    generation_policy: EnumManifestGenerationPolicy = EnumManifestGenerationPolicy.AutoOneForAll
    priority: EnumManifestPriority = EnumManifestPriority.Oldest

class LocalOutbox(IOSystem):
    data: LODataProfile
    manifests: LOManifestsProfile

class RIDataProfile(TapisIOSystemProfile, DataProfile):
    path: str = "/ETL/REMOTE-INBOX/DATA"

class RIManifestsProfile(TapisIOSystemProfile, ManifestsProfile):
    path: str = "/ETL/REMOTE-INBOX/MANIFESTS"
    generation_policy: EnumManifestGenerationPolicy = None
    priority: EnumManifestPriority = None

class RemoteInbox(IOSystem):
    data: RIDataProfile
    manifests: RIManifestsProfile

class TapisJobDef(BaseModel):
    pass

class TapisETLExtension(BaseModel):
    env_mappings: Dict[str, str] = {}
    last_status: str = "PENDING"

class TapisJobExtensions(BaseModel):
    tapis_etl: TapisETLExtension = TapisETLExtension()

class ExetendedTapisJob(TapisJobDef):
    extensions: TapisJobExtensions = TapisJobExtensions()

    class Config:
        extra = Extra.allow

ListOfStrMinOneItem = conlist(str, min_items=1)

class ActionFilter(BaseModel):
    pipeline_ids: ListOfStrMinOneItem = None
    run_async: bool = True

class TapisETLPipeline(Pipeline):
    before: ActionFilter = None
    remote_outbox: RemoteOutbox
    local_inbox: LocalInbox
    jobs: List[ExetendedTapisJob] = []
    local_outbox: LocalOutbox
    remote_inbox: RemoteInbox
    after: ActionFilter = None