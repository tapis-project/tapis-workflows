from typing import List

from pydantic import BaseModel, validator, Extra

from .requests import Pipeline

from backend.views.http.etl import (
    LocalInbox,
    LocalOutbox,
    RemoteInbox,
    RemoteOutbox
)


class TapisIOBox(BaseModel):
    system_id: str

class TapisRemoteInbox(TapisIOBox, RemoteInbox):
    pass

class TapisLocalInbox(TapisIOBox, LocalInbox):
    pass

class TapisLocalOutbox(TapisIOBox, LocalOutbox):
    pass

class TapisRemoteOutbox(TapisIOBox, RemoteOutbox):
    pass

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
    remote_outbox: TapisRemoteOutbox
    local_inbox: TapisLocalInbox
    jobs: List[ExetendedTapisJob]
    local_outbox: TapisLocalOutbox
    remote_inbox: TapisRemoteInbox

    @validator("jobs")
    def one_or_more_jobs(cls, value):
        # Check that the pipeline contains at least 1 tapis job definition
        if len(value) < 1:
            raise ValueError("A Tapis ETL pipeline must contain at least 1 Tapis Job definition")
        
        return value