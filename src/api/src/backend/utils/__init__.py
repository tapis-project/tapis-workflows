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
    if getattr(body.local_inbox, "data_integrity_profile", None) != None:
        local_inbox_data_integrity_profile = body.local_inbox.data_integrity_profile.dict()
    
    local_outbox_data_integrity_profile = {}
    if getattr(body.local_outbox, "data_integrity_profile", None) != None:
        local_outbox_data_integrity_profile = body.local_outbox.data_integrity_profile.dict()

    remote_inbox_data_integrity_profile = {}
    if getattr(body.remote_inbox, "data_integrity_profile", None) != None:
        remote_inbox_data_integrity_profile = body.remote_inbox.data_integrity_profile.dict()

    remote_outbox_data_integrity_profile = {}
    if getattr(body.remote_outbox, "data_integrity_profile", None) != None:
        remote_outbox_data_integrity_profile = body.remote_outbox.data_integrity_profile.dict()
        
    return {
        "REMOTE_OUTBOX": json.dumps(body.remote_outbox.dict()),
        "LOCAL_INBOX": json.dumps(body.local_inbox.dict()),
        "LOCAL_OUTBOX": json.dumps(body.local_outbox.dict()),
        "REMOTE_INBOX": json.dumps(body.remote_inbox.dict()),

        "REMOTE_OUTBOX_SYSTEM_ID": {
            "type": "string",
            "value": body.remote_outbox.system_id
        },
        "REMOTE_OUTBOX_DATA_PATH": {
            "type": "string",
            "value": body.remote_outbox.data_path
        },
        "REMOTE_OUTBOX_INCLUDE_PATTERN": {
            "type": "string",
            "value": body.remote_outbox.include_pattern
        },
        "REMOTE_OUTBOX_EXCLUDE_PATTERN": {
            "type": "string",
            "value": body.remote_outbox.exclude_pattern
        },
        "REMOTE_OUTBOX_MANIFESTS_PATH": {
            "type": "string",
            "value": body.remote_outbox.manifests_path
        },
        "REMOTE_OUTBOX_MANIFEST_GENERATION_POLICY": {
            "type": "string",
            "value": body.remote_outbox.manifest_generation_policy
        },
        "REMOTE_OUTBOX_MANIFEST_PRIORITY": {
            "type": "string",
            "value": body.remote_outbox.manifest_priority
        },
        "REMOTE_OUTBOX_DATA_INTEGRITY_TYPE": {
            "type": "string",
            "value": remote_outbox_data_integrity_profile.get(
                "type",
                None
            )
        },
        "REMOTE_OUTBOX_DATA_INTEGRITY_DONE_FILES_PATH": {
            "type": "string",
            "value": remote_outbox_data_integrity_profile.get(
                "done_files_path",
                None
            )
        },
        "REMOTE_OUTBOX_DATA_INTEGRITY_DONE_FILE_INCLUDE_PATTERN": {
            "type": "string",
            "value": remote_outbox_data_integrity_profile.get(
                "include_pattern",
                None
            )
        },
        "REMOTE_OUTBOX_DATA_INTEGRITY_DONE_FILE_EXCLUDE_PATTERN": {
            "type": "string",
            "value": remote_outbox_data_integrity_profile.get(
                "exclude_pattern",
                None
            )
        },
        
        "LOCAL_INBOX_SYSTEM_ID": {
            "type": "string",
            "value": body.local_inbox.system_id
        },
        "LOCAL_INBOX_DATA_PATH": {
            "type": "string",
            "value": body.local_inbox.data_path
        },
        "LOCAL_INBOX_INCLUDE_PATTERN": {
            "type": "string",
            "value": body.local_inbox.include_pattern
        },
        "LOCAL_INBOX_EXCLUDE_PATTERN": {
            "type": "string",
            "value": body.local_inbox.exclude_pattern
        },
        "LOCAL_INBOX_MANIFESTS_PATH": {
            "type": "string",
            "value": body.local_inbox.manifests_path
        },
        "LOCAL_INBOX_DATA_INTEGRITY_TYPE": {
            "type": "string",
            "value": local_inbox_data_integrity_profile.get(
                "type",
                None
            )
        },
        "LOCAL_INBOX_DATA_INTEGRITY_DONE_FILES_PATH": {
            "type": "string",
            "value": local_inbox_data_integrity_profile.get(
                "done_files_path",
                None
            )
        },
        "LOCAL_INBOX_DATA_INTEGRITY_DONE_FILE_INCLUDE_PATTERN": {
            "type": "string",
            "value": local_inbox_data_integrity_profile.get(
                "include_pattern",
                None
            )
        },
        "LOCAL_INBOX_DATA_INTEGRITY_DONE_FILE_EXCLUDE_PATTERN": {
            "type": "string",
            "value": local_inbox_data_integrity_profile.get(
                "exclude_pattern",
                None
            )
        },

        "LOCAL_OUTBOX_SYSTEM_ID": {
            "type": "string",
            "value": body.local_outbox.system_id
        },
        "LOCAL_OUTBOX_DATA_PATH": {
            "type": "string",
            "value": body.local_outbox.data_path
        },
        "LOCAL_OUTBOX_INCLUDE_PATTERN": {
            "type": "string",
            "value": body.local_outbox.include_pattern
        },
        "LOCAL_OUTBOX_EXCLUDE_PATTERN": {
            "type": "string",
            "value": body.local_outbox.exclude_pattern
        },
        "LOCAL_OUTBOX_MANIFESTS_PATH": {
            "type": "string",
            "value": body.local_outbox.manifests_path
        },
        "LOCAL_OUTBOX_MANIFEST_GENERATION_POLICY": {
            "type": "string",
            "value": body.local_outbox.manifest_generation_policy
        },
        "LOCAL_OUTBOX_MANIFEST_PRIORITY": {
            "type": "string",
            "value": body.local_outbox.manifest_priority
        },
        "LOCAL_OUTBOX_DATA_INTEGRITY_TYPE": {
            "type": "string",
            "value": local_outbox_data_integrity_profile.get(
                "type",
                None
            )
        },
        "LOCAL_OUTBOX_DATA_INTEGRITY_DONE_FILES_PATH": {
            "type": "string",
            "value": local_outbox_data_integrity_profile.get(
                "done_files_path",
                None
            )
        },
        "LOCAL_OUTBOX_DATA_INTEGRITY_DONE_FILE_INCLUDE_PATTERN": {
            "type": "string",
            "value": local_outbox_data_integrity_profile.get(
                "include_pattern",
                None
            )
        },
        "LOCAL_OUTBOX_DATA_INTEGRITY_DONE_FILE_EXCLUDE_PATTERN": {
            "type": "string",
            "value": local_outbox_data_integrity_profile.get(
                "exclude_pattern",
                None
            )
        },

        "REMOTE_INBOX_SYSTEM_ID": {
            "type": "string",
            "value": body.remote_inbox.system_id
        },
        "REMOTE_INBOX_DATA_PATH": {
            "type": "string",
            "value": body.remote_inbox.data_path
        },
        "REMOTE_INBOX_INCLUDE_PATTERN": {
            "type": "string",
            "value": body.remote_inbox.include_pattern
        },
        "REMOTE_INBOX_EXCLUDE_PATTERN": {
            "type": "string",
            "value": body.remote_inbox.exclude_pattern
        },
        "REMOTE_INBOX_MANIFESTS_PATH": {
            "type": "string",
            "value": body.remote_inbox.manifests_path
        },
        "REMOTE_INBOX_DATA_INTEGRITY_TYPE": {
            "type": "string",
            "value": remote_inbox_data_integrity_profile.get(
                "type",
                None
            )
        },
        "REMOTE_INBOX_DATA_INTEGRITY_DONE_FILES_PATH": {
            "type": "string",
            "value": remote_inbox_data_integrity_profile.get(
                "done_files_path",
                None
            )
        },
        "REMOTE_INBOX_DATA_INTEGRITY_DONE_FILE_INCLUDE_PATTERN": {
            "type": "string",
            "value": remote_inbox_data_integrity_profile.get(
                "include_pattern",
                None
            )
        },
        "REMOTE_INBOX_DATA_INTEGRITY_DONE_FILE_EXCLUDE_PATTERN": {
            "type": "string",
            "value": remote_inbox_data_integrity_profile.get(
                "exclude_pattern",
                None
            )
        },
    }

    