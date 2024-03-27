import json

from backend.conf.constants import (
    DJANGO_WORKFLOW_EXECUTOR_TOKEN_HEADER,
    WORKFLOW_EXECUTOR_ACCESS_TOKEN
)


def one_in(strings, target):
    for string in strings:
        if string in target:
            return True
    return False

def executor_request_is_valid(request):
    # Check that the X-WORKFLOW-EXECUTOR-TOKEN header is set
    if DJANGO_WORKFLOW_EXECUTOR_TOKEN_HEADER not in request.META:
        return False

    executor_token = request.META[DJANGO_WORKFLOW_EXECUTOR_TOKEN_HEADER]
    if executor_token != WORKFLOW_EXECUTOR_ACCESS_TOKEN:
        return False

    return True

def build_etl_pipeline_env(body):
    # Convert the data integrity policies to dicts. Easier
    # to handle for null values via .get
    local_inbox_data_integrity_profile = {}
    if getattr(body.local_inbox.data, "integrity_profile", None) != None:
        local_inbox_data_integrity_profile = body.local_inbox.data.integrity_profile.dict()
    
    local_outbox_data_integrity_profile = {}
    if getattr(body.local_outbox.data, "integrity_profile", None) != None:
        local_outbox_data_integrity_profile = body.local_outbox.data.integrity_profile.dict()

    remote_inbox_data_integrity_profile = {}
    if getattr(body.remote_inbox.data, "integrity_profile", None) != None:
        remote_inbox_data_integrity_profile = body.remote_inbox.data.integrity_profile.dict()

    remote_outbox_data_integrity_profile = {}
    if getattr(body.remote_outbox.data, "integrity_profile", None) != None:
        remote_outbox_data_integrity_profile = body.remote_outbox.data.integrity_profile.dict()

    body.local_inbox.data.integrity_profile = local_inbox_data_integrity_profile
    body.local_outbox.data.integrity_profile = local_outbox_data_integrity_profile
    body.remote_outbox.data.integrity_profile = remote_outbox_data_integrity_profile
    body.remote_inbox.data.integrity_profile = remote_inbox_data_integrity_profile
        
    return {
        "REMOTE_OUTBOX": {
            "type": "string",
            "value": json.dumps(body.remote_outbox.dict())
        },
        "LOCAL_INBOX": {
            "type": "string",
            "value": json.dumps(body.local_inbox.dict())
        },
        "LOCAL_OUTBOX": {
            "type": "string",
            "value": json.dumps(body.local_outbox.dict())
        },
        "REMOTE_INBOX": {
            "type": "string",
            "value": json.dumps(body.remote_inbox.dict())
        },
        "DEFAULT_ETL_JOBS": {
            "type": "string",
            "value": json.dumps(body.jobs)
        }
    }

    