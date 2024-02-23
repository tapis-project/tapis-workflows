from typing import List

from pydantic import BaseModel, validator, Extra, root_validator

from .requests import Pipeline

from backend.views.http.etl import (
    EnumManifestGenerationPolicy,
    EnumManifestPriority,
    IOSystem
)

class TapisIOBox(IOSystem):
    writable_system_id: str = None
    data_transfer_system_id: str = None

    @root_validator
    def validate_system_ids(cls, values):
        if (
            values.get("writable_system_id") == None
            and values.get("data_transfer_system_id") == None
        ):
            raise ValueError("Must define one or both of the following properties: ['writable_system_id', 'data_transfer_system_id']")

        return values
    
class TapisRemoteOutbox(TapisIOBox):
    manifest_generation_policy: EnumManifestGenerationPolicy = None
    manifest_priority: EnumManifestPriority = EnumManifestPriority.Oldest
    data_path: str = "/ETL/REMOTE-OUTBOX/DATA"
    manifests_path: str = "/ETL/REMOTE-OUTBOX/MANFIFESTS"

class TapisLocalInbox(TapisIOBox):
    manifest_generation_policy: EnumManifestGenerationPolicy = EnumManifestGenerationPolicy.AutoOnePerFile
    manifest_priority: EnumManifestPriority = EnumManifestPriority.Oldest
    data_path: str = "/ETL/LOCAL-INBOX/DATA"
    manifests_path: str = "/ETL/LOCAL-INBOX/MANFIFESTS"
    inbound_transfer_manifests_path: str = "/ETL/LOCAL-INBOX/"

class TapisLocalOutbox(TapisIOBox):
    manifest_generation_policy: EnumManifestGenerationPolicy = EnumManifestGenerationPolicy.AutoOneForAll
    manifest_priority: EnumManifestPriority = EnumManifestPriority.Oldest
    data_path: str = "/ETL/LOCAL-INBOX/DATA"
    manifests_path: str = "/ETL/LOCAL-INBOX/MANFIFESTS"

class TapisRemoteInbox(TapisIOBox):
    manifest_generation_policy: EnumManifestGenerationPolicy = None
    manifest_priority: EnumManifestPriority = None
    data_path: str = "/ETL/REMOTE-INBOX/DATA"
    manifests_path: str = "/ETL/REMOTE-INBOX/MANFIFESTS"


class TapisJobDef(BaseModel):
    pass

class TapisJobWorkflowsETL(BaseModel):
    input: str
    output: str

class TapisJobWorkflowsExtension(BaseModel):
    etl: TapisJobWorkflowsETL

class ExetendedTapisJob(TapisJobDef):
    workflows: TapisJobWorkflowsExtension = None

    class Config:
        extra = Extra.allow

class TapisETLPipeline(Pipeline):
    run_before: List[str] = []
    remote_outbox: TapisRemoteOutbox
    local_inbox: TapisLocalInbox
    jobs: List[ExetendedTapisJob]
    local_outbox: TapisLocalOutbox
    remote_inbox: TapisRemoteInbox
    run_after: List[str] = []

    @validator("jobs")
    def one_or_more_jobs(cls, value):
        # Check that the pipeline contains at least 1 tapis job definition
        if len(value) < 1:
            raise ValueError("A Tapis ETL pipeline must contain at least 1 Tapis Job definition")
        
        return value