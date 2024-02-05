from .tasks import request, image_build

standard_workflow = {
    "id": "p1",
    "type": "workflow",
    "archive_ids": [],
    "tasks": [image_build, request],
    "env": {
        "TAPIS_SYSTEM_ID": {
            "type": "string",
            "value": "my-system-id"
        },
        "MANIFEST_FILES_PATH": {
            "type": "string",
            "value": "/"
        },
        "TAPIS_USERNAME": {
            "type": "string",
            "value": "testuser2"
        },
        "TAPIS_PASSWORD": {
            "type": "string",
            "value": "testuser2"
        }
    }
}